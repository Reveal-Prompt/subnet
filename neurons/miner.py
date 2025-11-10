import time
import typing
import bittensor as bt
from google import genai
import template
import requests
import os
from template.base.miner import BaseMinerNeuron
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class Miner(BaseMinerNeuron):

    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)
        bt.logging.info(" Miner initialized successfully.")

    def generate_prompt(self, path_to_image: str):
        try:
            bt.logging.info(f"  Starting prompt generation")

            # Fetch image
            if path_to_image.startswith("http://") or path_to_image.startswith("https://"):
                bt.logging.debug("Fetching image from URL...")
                response = requests.get(path_to_image)
                response.raise_for_status()
                image_bytes = response.content
                bt.logging.info(" Image fetched successfully from URL.")
            else:
                bt.logging.debug("Reading image from local path...")
                with open(path_to_image, 'rb') as f:
                    image_bytes = f.read()
                bt.logging.info(" Image loaded from local file.")

            # Connect to Gemini API
            api_key = os.getenv("GEMENI_API")
            if not api_key:
                bt.logging.error(" Missing GEMENI_API key in environment.")
                raise ValueError("Missing GEMENI_API key in .env file")

            bt.logging.debug("Initializing Gemini client...")
            client = genai.Client(api_key=api_key)

            # Generate prompt
            bt.logging.info("  Sending image to Gemini model for prompt generation...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                    'Generate a detailed prompt describing the image above and remember to limit the description to 100 words only'
                ]
            )

            bt.logging.info(" Prompt generated successfully.")
            bt.logging.debug(f"Model Response: {response.text[:200]}...")  # preview first 200 chars
            return response.text

        except requests.exceptions.RequestException as re:
            bt.logging.error(f" Network error while fetching image: {re}")
            raise
        except Exception as e:
            bt.logging.error(f" Error during prompt generation: {e}", exc_info=True)
            raise

    async def forward(
        self, synapse: template.protocol.ReversePrompt
    ) -> template.protocol.ReversePrompt:
        bt.logging.info(" Forward function triggered.")
        try:
            bt.logging.debug(f"Received synapse with image path: {synapse.path_to_image}")
            generated_prompt = self.generate_prompt(synapse.path_to_image)
            synapse.output = generated_prompt
            bt.logging.info(" Synapse processed successfully.")
            bt.logging.debug(f"Generated Prompt Output: {generated_prompt[:200]}...")
            return synapse
        except Exception as e:
            bt.logging.error(f" Error in forward() execution: {e}", exc_info=True)
            raise e


    async def blacklist(
        self, synapse: template.protocol.ReversePrompt
    ) -> typing.Tuple[bool, str]:
       

        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning(
                "Received a request without a dendrite or hotkey."
            )
            return True, "Missing dendrite or hotkey"

        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if (
            not self.config.blacklist.allow_non_registered
            and synapse.dendrite.hotkey not in self.metagraph.hotkeys
        ):
            # Ignore requests from un-registered entities.
            bt.logging.trace(
                f"Blacklisting un-registered hotkey {synapse.dendrite.hotkey}"
            )
            return True, "Unrecognized hotkey"

        if self.config.blacklist.force_validator_permit:
            if not self.metagraph.validator_permit[uid]:
                bt.logging.warning(
                    f"Blacklisting a request from non-validator hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Non-validator hotkey"

        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    async def priority(self, synapse: template.protocol.ReversePrompt) -> float:
      
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning(
                "Received a request without a dendrite or hotkey."
            )
            return 0.0

        # TODO(developer): Define how miners should prioritize requests.
        caller_uid = self.metagraph.hotkeys.index(
            synapse.dendrite.hotkey
        )  # Get the caller index.
        priority = float(
            self.metagraph.S[caller_uid]
        )  # Return the stake as the priority.
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: {priority}"
        )
        return priority




if __name__ == "__main__":
    with Miner() as miner:
        bt.logging.info(" Miner is now active and ready to process requests.")
        while True:
            time.sleep(5)
