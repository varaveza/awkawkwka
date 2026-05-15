# Silicoin (SLC) Miner

Simple JavaScript PoW miner for Silicoin (SLC) on Ethereum mainnet.

## Contract
- Address: `0xbb572707D09eB2E80C835D3051097E5083D460Cc`
- Chain: Ethereum mainnet
- Reward: 1000 SLC per win (epoch 0)

## Setup

```bash
npm install
cp .env.example .env
# Edit .env - add PRIVATE_KEY
npm run mine
```

## Performance

- **JS (current)**: ~50k H/s - too slow for current difficulty
- **Native (Rust)**: ~10M H/s - 200x faster
- **GPU (OpenCL/CUDA)**: ~1000M H/s - 20,000x faster

**Recommendation:** Use GPU on Vast.ai or similar for realistic mining.

## Config (.env)

```
PRIVATE_KEY=0x...           # Required: dedicated hot wallet
RPC_URL=https://...         # Optional: default public RPC
MAX_GAS_GWEI=20            # Optional: pause if gas > this
BUDGET_ETH=0.02            # Optional: stop after spending this much
```

## Features

- ✅ Auto-loop until budget exhausted
- ✅ Auto-submit commit+reveal on win
- ✅ Pause when gas too high
- ✅ Track wins, SLC mined, gas spent
- ✅ Final report

## Notes

- Mining only costs gas when you win (~200k gas = ~$0.01-0.10 depending on gas price)
- No deposits, no approvals - wallet only receives SLC
- Pool is live, difficulty is high (GPU-optimized)
