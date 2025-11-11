# ⚙️ Prerequisites & Setup

Welcome to Reveal Prompt! This guide will walk you through setting up your development environment, whether you're on Windows, Linux, or macOS. Follow these steps carefully to get your miner or validator running smoothly.

## 📋 System Requirements

Before you begin, ensure your system meets these minimum requirements:

- **CPU**: 4+ cores (8+ cores recommended for validators)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 50GB available space
- **Network**: Stable internet connection with low latency
- **OS**: Windows 10/11 (with WSL2), Linux (Ubuntu 20.04+), or macOS 11+

---

## 🪟 Windows Users: Install WSL2

If you're on Windows, you'll need Windows Subsystem for Linux (WSL2) to run Bittensor and Reveal Prompt.

**Installation & Setup Resources**:
- 📖 [Microsoft WSL Installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install)
- 📖 [Manual Installation Steps](https://learn.microsoft.com/en-us/windows/wsl/install-manual) (if automatic install fails)
- 📖 [WSL Basic Commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)
- 📖 [Best Practices for WSL](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)
- 📖 [Troubleshooting WSL](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting)

Once WSL2 is installed and you have Ubuntu set up, continue with the Linux instructions below inside your WSL2 terminal.

---


### Python Installation

Ensure you have Python 3.8 or higher installed:

**Python Resources**:
- 📖 [Python Downloads](https://www.python.org/downloads/)
- 📖 [Python Installation Guide for Linux](https://docs.python.org/3/using/unix.html)
- 📖 [Python Installation Guide for macOS](https://docs.python.org/3/using/mac.html)

You can verify your Python installation with `python3 --version`.

---

## 📦 Install Poetry

Poetry is our package manager of choice. It handles dependencies and virtual environments automatically.

**Installation & Setup Resources**:
- 📖 [Official Poetry Installation Guide](https://python-poetry.org/docs/#installation)
- 📖 [Installing with pipx](https://python-poetry.org/docs/#installing-with-pipx) (recommended for isolated installation)
- 📖 [PATH Configuration Guide](https://python-poetry.org/docs/#installation)

After installing Poetry and ensuring it's in your PATH, verify the installation with `poetry --version`.

---

## 🔧 Clone & Set Up the Repository

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/reveal-prompt.git
cd reveal-prompt
```

### Step 2: Install Dependencies with Poetry

Poetry will create a virtual environment and install all dependencies automatically:

```bash
poetry install
```

This may take a few minutes as it downloads and installs all required packages, including Bittensor.

### Step 3: Activate the Poetry Shell

Enter the Poetry-managed virtual environment:

```bash
poetry shell
```

Your terminal prompt will change to indicate you're inside the virtual environment. You'll need to stay in this shell to run miners and validators.

---


## 👛 Set Up Your Bittensor Wallet

Before running miners or validators, you need a Bittensor wallet. The `btcli` (Bittensor CLI) tool makes this easy.

### Step 1: Verify btcli Installation

btcli should be installed automatically with Poetry. Verify it's available:

```bash
btcli --help
```

If you see the help menu, you're good to go!

### Step 2: Create a New Wallet

Create a new coldkey (your main wallet):

```bash
btcli wallet new_coldkey --wallet.name miner
```

You'll be prompted to set a password. **Write this down securely** - you'll need it to access your funds.

### Step 3: Create a Hotkey

Create a hotkey (used for subnet operations):

```bash
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default
```

### Step 4: Get Testnet TAO (For Testing)

If you're testing on the testnet, you'll need testnet TAO. Join the [Bittensor Discord](https://discord.gg/bittensor) and request testnet tokens in the faucet channel.

### Step 5: Register on the Subnet

Register your hotkey on the Reveal Prompt subnet:

```bash
btcli subnet register --netuid X --subtensor.network test --wallet.name miner --wallet.hotkey default
```

Replace `X` with the actual subnet ID for Reveal Prompt.

---

## 🚀 Running Your Node

Now that everything is set up, you can start running your miner or validator!

### 🔨 Running a Miner

Miners analyze AI outputs and reveal hidden prompts to earn rewards.


**For Testnet:**

```bash
python -m neurons.miner --netuid 395 \
    --subtensor.network test \
    --wallet.name <your_miner_wallet> \
    --axon.port <port> \
    --axon.ip <ip_address> \
    --subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
    --logging.info
```

**For Mainnet:**

```bash
python -m neurons.miner --netuid <netuid> \
    --subtensor.network main \
    --wallet.name <your_miner_wallet> \
    --axon.port <port> \
    --axon.ip <ip_address> \
    --subtensor.chain_endpoint wss://finney.opentensor.ai:443 \
    --logging.info
```

### ⚖️ Running a Validator

Validators generate test outputs, score miner responses, and set weights.

**Prerequisites for Validators:**
- Minimum 1000 TAO stake recommended
- Higher hardware requirements (see System Requirements above)



**For Testnet:**

```bash
python -m neurons.validator --netuid 395 \
    --subtensor.network test \
    --wallet.name <your_validator_wallet> \
    --axon.port <port> \
    --axon.ip <ip_address> \
    --subtensor.chain_endpoint wss://test.finney.opentensor.ai:443 \
    --logging.info
```

**For Mainnet:**

```bash
python -m neurons.validator --netuid <netuid> \
    --subtensor.network main \
    --wallet.name <your_validator_wallet> \
    --axon.port <port> \
    --axon.ip <ip_address> \
    --subtensor.chain_endpoint wss://finney.opentensor.ai:443 \
    --logging.info
```

---

## 🛠️ Common Commands

Here are some useful commands you'll use frequently:

### Poetry Commands

```bash
# Activate the virtual environment
poetry shell

# Install/update dependencies
poetry install

# Add a new dependency
poetry add package-name

# Run a command in the Poetry environment without activating shell
poetry run python script.py

# Update all dependencies
poetry update

# Exit the Poetry shell
exit
```

### Bittensor CLI Commands

```bash
# Check wallet balance
btcli wallet balance --wallet.name miner

# View subnet information
btcli subnet list --subtensor.network test

# Check your registration status
btcli subnet metagraph --netuid X --subtensor.network test

# View your stake
btcli stake show --wallet.name miner
```

---

### Connection Issues

If you're having trouble connecting to the network:

1. Check your internet connection
2. Verify the subnet is active: `btcli subnet list --subtensor.network test`
3. Ensure your firewall isn't blocking connections
4. For validators, make sure the axon port (default 8091) is open

---

## 💡 Tips for Success

- **Start on Testnet**: Always test your setup on testnet before moving to mainnet
- **Monitor Logs**: Keep an eye on your logs to catch issues early
- **Stay Updated**: Regularly pull the latest changes from the repository
- **Backup Your Wallet**: Store your mnemonic phrase and passwords securely offline
- **Join the Discussion**: The community is friendly and helpful - don't hesitate to ask questions!

---

**Ready to reveal some prompts? Let's go! 🚀**
