import time
import torch
from PIL import Image
import bittensor as bt
from transformers import CLIPProcessor, CLIPModel
from template.base.validator import BaseValidatorNeuron
from template.protocol import ReversePrompt
import numpy as np
import requests
from io import BytesIO
import torch.nn.functional as F
from torchvision import transforms
from lpips import LPIPS
from openai import OpenAI
import asyncio
from dotenv import load_dotenv
import os
import nest_asyncio

nest_asyncio.apply()

load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize LPIPS model once
bt.logging.info("Initializing LPIPS model...")
lpips_model = LPIPS(net='vgg').to(device)
lpips_model.eval()
bt.logging.info("LPIPS model loaded and ready.")

# Setup CLIP Model once
bt.logging.info("Loading CLIP model and processor...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
bt.logging.info("CLIP model initialized successfully.")

# OpenAI client setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    bt.logging.warning("OPENAI_API_KEY not found in environment variables. Image generation may fail.")

class Validator(BaseValidatorNeuron):
    def __init__(self, config=None):
        super().__init__(config=config)
        bt.logging.info("Validator initialized successfully.")
        self.load_state()

    def generateimage(self, prompt: str) -> str:
        """Generate reference image using OpenAI API."""
        # bt.logging.info(f"Generating base image for prompt")
        try:
            result = client.images.generate(model="dall-e-2", prompt=prompt)
            image_url = result.data[0].url
            return image_url
        except Exception as e:
            bt.logging.error(f"Image generation failed for prompt '{prompt}': {e}", exc_info=True)
            raise

    async def forward(self):
        """Main validator logic for evaluating miner responses."""
        # bt.logging.info("Starting forward pass for validator.")
        try:
            prompt = "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
            ref_image_url = self.generateimage(prompt)
            bt.logging.info(f"Reference image URL generated")

            bt.logging.info("Sending ReversePrompt requests to miners...")
            responses = await self.dendrite.forward(
                axons=self.metagraph.axons,
                synapse=ReversePrompt(path_to_image=ref_image_url),
                timeout=10,
            )

            bt.logging.info(f"Received responses from {len(responses)} miners.")
            rewards = {}
            miner_uids = []

            for uid, response in enumerate(responses):
                if response is None:
                    bt.logging.warning(f"Miner {uid} returned no response. Setting reward to 0.0.")
                    rewards[uid] = 0.0
                    continue

                try:
                    candidate_url = self.generateimage(response)
                    reward = await asyncio.to_thread(self.get_rewards, ref_image_url, candidate_url)
                    bt.logging.info(f"Miner {uid}: reward computed successfully -> {reward:.4f}")
                    rewards[uid] = reward
                    miner_uids.append(uid)
                except Exception as e:
                    bt.logging.error(f"Failed to compute reward for miner {uid}: {e}", exc_info=True)
                    rewards[uid] = 0.0

            bt.logging.info(f"Rewards dictionary: {rewards}")

            if isinstance(rewards, dict):
                rewards_list = [float(rewards.get(uid, 0.0)) for uid in miner_uids]
                rewards_array = np.array(rewards_list, dtype=float)
                rewards_for_update = dict(zip(miner_uids, rewards_list))
            else:
                rewards_array = np.array(rewards, dtype=float)
                if miner_uids and len(miner_uids) == rewards_array.shape[0]:
                    rewards_for_update = dict(zip(miner_uids, rewards_array.tolist()))
                else:
                    rewards_for_update = {i: float(v) for i, v in enumerate(rewards_array.tolist())}

            if np.isnan(rewards_array).any():
                bt.logging.warning("NaN values detected in rewards. Replacing with 0.0.")
                rewards_array = np.nan_to_num(rewards_array, nan=0.0)
                rewards_for_update = {i: float(v) for i, v in enumerate(rewards_array.tolist())}

            self.update_scores(rewards_for_update, miner_uids)
            bt.logging.info("Validator scores updated successfully.")
            await asyncio.sleep(5)
            return responses

        except Exception as e:
            bt.logging.error(f"Forward function failed: {e}", exc_info=True)
            raise

    def get_rewards(self, reference_path: str, candidate_path: str) -> float:
        """Compute CLIP cosine similarity + LPIPS perceptual similarity."""
        bt.logging.debug(f"Starting reward computation")
        try:
            def load_image(path):
                if path.startswith("http://") or path.startswith("https://"):
                    response = requests.get(path, timeout=10)
                    response.raise_for_status()
                    return Image.open(BytesIO(response.content)).convert("RGB")
                return Image.open(path).convert("RGB")

            ref_img = load_image(reference_path)
            cand_img = load_image(candidate_path)

            # CLIP semantic similarity
            inputs = clip_processor(images=[ref_img, cand_img], return_tensors="pt").to(device)
            with torch.no_grad():
                feats = clip_model.get_image_features(**inputs)
                feats = feats / feats.norm(p=2, dim=-1, keepdim=True)
                cosine_sim = torch.matmul(feats[0], feats[1]).item()
                clip_score = (cosine_sim + 1) / 2

            # LPIPS perceptual similarity
            preprocess = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor()
            ])
            ref_t = preprocess(ref_img).unsqueeze(0).to(device)
            cand_t = preprocess(cand_img).unsqueeze(0).to(device)
            with torch.no_grad():
                perceptual_diff = lpips_model(ref_t, cand_t).item()
            perceptual_score = max(0.0, 1 - perceptual_diff)

            combined = 0.7 * clip_score + 0.3 * perceptual_score
            reward = float(np.clip(combined ** 3, 0.0001, 1.0))

            bt.logging.debug(f"CLIP Score: {clip_score:.4f}, LPIPS Score: {perceptual_score:.4f}, Final Reward: {reward:.4f}")
            return reward

        except Exception as e:
            bt.logging.error(f"Reward computation failed: {e}", exc_info=True)
            return 0.0

    def update_scores(self, rewards: dict, miner_uids: list):
        """Update validator scores for miners."""
        bt.logging.info("Updating miner scores...")
        for uid, score in zip(miner_uids, rewards.values()):
            self.scores[uid] = score
            bt.logging.debug(f"Miner {uid}: new score = {self.scores[uid]:.4f}")
        self.set_weights()
        bt.logging.info("All miner scores updated successfully.")



if __name__ == "__main__":
    with Validator() as validator:
        bt.logging.info("Validator started and ready to process miners.")
        while True:
            # bt.logging.info(f"Validator running at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            # try:
            #     validator.run()
            # except Exception as e:
            #     bt.logging.error(f"Validator runtime error: {e}", exc_info=True)
            time.sleep(5)

