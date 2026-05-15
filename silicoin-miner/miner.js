import { createPublicClient, createWalletClient, http, parseAbi, keccak256, encodePacked, formatEther } from 'viem';
import { mainnet } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import 'dotenv/config';

const SLC_ADDRESS = '0xbb572707D09eB2E80C835D3051097E5083D460Cc';
const RPC_URL = process.env.RPC_URL || 'https://eth.llamarpc.com';
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const MAX_GAS_GWEI = BigInt(process.env.MAX_GAS_GWEI || '20');
const BUDGET_ETH = parseFloat(process.env.BUDGET_ETH || '0.02');

if (!PRIVATE_KEY) {
  console.error('❌ PRIVATE_KEY required in .env');
  process.exit(1);
}

const account = privateKeyToAccount(PRIVATE_KEY);
const publicClient = createPublicClient({ chain: mainnet, transport: http(RPC_URL) });
const walletClient = createWalletClient({ chain: mainnet, transport: http(RPC_URL), account });

const abi = parseAbi([
  'function mineParams() view returns (bytes32 epochSeed, uint256 target, uint256 reward, uint8 epoch, bool poolLive)',
  'function commit(bytes32 commitment) external',
  'function reveal(uint256 nonce, bytes32 secret, uint256 anchorBlock) external',
  'function balanceOf(address) view returns (uint256)',
  'function totalMined() view returns (uint256)',
]);

let totalGasSpent = 0;
let totalWins = 0;
let totalSlcMined = 0n;

console.log(`🔑 Wallet: ${account.address}`);
console.log(`💰 Budget: ${BUDGET_ETH} ETH`);
console.log(`⛽ Max gas: ${MAX_GAS_GWEI} gwei\n`);

// Check status
async function getStatus() {
  const [params, balance, totalMined, gasPrice, ethBalance] = await Promise.all([
    publicClient.readContract({ address: SLC_ADDRESS, abi, functionName: 'mineParams' }),
    publicClient.readContract({ address: SLC_ADDRESS, abi, functionName: 'balanceOf', args: [account.address] }),
    publicClient.readContract({ address: SLC_ADDRESS, abi, functionName: 'totalMined' }),
    publicClient.getGasPrice(),
    publicClient.getBalance({ address: account.address }),
  ]);

  const [epochSeed, target, reward, epoch, poolLive] = params;
  
  return { params, balance, totalMined, gasPrice, ethBalance, poolLive };
}

// Search for valid nonce
function searchNonce(challenge, target, minerAddr) {
  const targetBigInt = BigInt(target);
  let nonce = BigInt(Math.floor(Math.random() * 1e15)); // Random start
  let attempts = 0;
  const maxAttempts = 1000000; // Try 1M hashes per round

  while (attempts < maxAttempts) {
    const hash = keccak256(encodePacked(
      ['bytes32', 'address', 'uint256'],
      [challenge, minerAddr, nonce]
    ));
    
    const hashValue = BigInt(hash);
    
    if (hashValue < targetBigInt) {
      return { nonce, attempts: attempts + 1 };
    }
    
    nonce++;
    attempts++;
  }

  return null; // No solution found in this round
}

// Single mining attempt
async function mineOnce() {
  const { params, balance, gasPrice, ethBalance, poolLive } = await getStatus();
  
  if (!poolLive) {
    console.log('❌ Pool not live yet. Waiting...');
    await new Promise(r => setTimeout(r, 60000)); // Wait 1 min
    return false;
  }

  const gasPriceGwei = Number(gasPrice) / 1e9;
  if (gasPriceGwei > Number(MAX_GAS_GWEI)) {
    console.log(`⏸️  Gas too high (${gasPriceGwei.toFixed(2)} gwei). Waiting...`);
    await new Promise(r => setTimeout(r, 30000)); // Wait 30s
    return false;
  }

  const [epochSeed, target, reward, epoch] = params;
  
  // Get anchor block
  const latestBlock = await publicClient.getBlockNumber();
  const anchorBlock = latestBlock - 2n;
  const anchorBlockData = await publicClient.getBlock({ blockNumber: anchorBlock });
  const anchorHash = anchorBlockData.hash;
  
  // Calculate challenge
  const challenge = keccak256(encodePacked(['bytes32', 'bytes32'], [anchorHash, epochSeed]));
  
  // Search for nonce
  const startTime = Date.now();
  const result = searchNonce(challenge, target, account.address);
  const elapsed = (Date.now() - startTime) / 1000;
  
  if (!result) {
    const hashrate = Math.floor(1000000 / elapsed);
    console.log(`⛏️  No solution (1M attempts, ${hashrate.toLocaleString()} H/s) | Gas spent: ${totalGasSpent.toFixed(6)}/${BUDGET_ETH} ETH | Wins: ${totalWins}`);
    return false;
  }
  
  const { nonce, attempts } = result;
  const hashrate = Math.floor(attempts / elapsed);
  console.log(`✅ Found nonce after ${attempts.toLocaleString()} attempts (${hashrate.toLocaleString()} H/s)`);
  
  // Re-check params
  const newParams = await publicClient.readContract({ address: SLC_ADDRESS, abi, functionName: 'mineParams' });
  if (newParams[0] !== epochSeed || newParams[1] !== target) {
    console.log('⚠️  Params changed. Discarding solution.');
    return false;
  }
  
  // Generate secret and commitment
  const secret = keccak256(encodePacked(['uint256'], [BigInt(Math.floor(Math.random() * 1e18))]));
  const commitment = keccak256(encodePacked(
    ['uint256', 'bytes32', 'address', 'uint256'],
    [nonce, secret, account.address, anchorBlock]
  ));
  
  try {
    // Submit commit
    console.log('📤 Submitting commit...');
    const commitHash = await walletClient.writeContract({
      address: SLC_ADDRESS,
      abi,
      functionName: 'commit',
      args: [commitment],
    });
    
    const commitReceipt = await publicClient.waitForTransactionReceipt({ hash: commitHash });
    const commitBlock = commitReceipt.blockNumber;
    
    console.log(`✓ Commit in block ${commitBlock}`);
    
    // Submit reveal
    console.log('📤 Submitting reveal...');
    const revealHash = await walletClient.writeContract({
      address: SLC_ADDRESS,
      abi,
      functionName: 'reveal',
      args: [nonce, secret, anchorBlock],
    });
    
    const revealReceipt = await publicClient.waitForTransactionReceipt({ hash: revealHash });
    
    if (revealReceipt.status === 'success') {
      const gasUsed = (Number(revealReceipt.gasUsed) + Number(commitReceipt.gasUsed)) * Number(gasPrice) / 1e18;
      totalGasSpent += gasUsed;
      totalWins++;
      totalSlcMined += reward;
      
      console.log(`\n🎉 WIN #${totalWins}! Mined ${reward} SLC`);
      console.log(`   Gas: ${gasUsed.toFixed(6)} ETH | Total: ${totalGasSpent.toFixed(6)}/${BUDGET_ETH} ETH`);
      console.log(`   Total mined: ${totalSlcMined} SLC`);
      console.log(`   Tx: ${revealHash}\n`);
      
      return true;
    } else {
      console.log('❌ Reveal failed');
      return false;
    }
    
  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    return false;
  }
}

// Main loop
async function mine() {
  console.log('🚀 Starting auto-miner...\n');
  
  while (totalGasSpent < BUDGET_ETH) {
    try {
      await mineOnce();
      
      // Check if budget exceeded
      if (totalGasSpent >= BUDGET_ETH) {
        console.log(`\n🛑 Budget reached (${totalGasSpent.toFixed(6)} ETH)`);
        break;
      }
      
      // Small delay between rounds
      await new Promise(r => setTimeout(r, 1000));
      
    } catch (error) {
      console.error(`❌ Loop error: ${error.message}`);
      await new Promise(r => setTimeout(r, 5000)); // Wait 5s on error
    }
  }
  
  // Final report
  const { balance, ethBalance } = await getStatus();
  console.log('\n📊 Final Report:');
  console.log(`   Wins: ${totalWins}`);
  console.log(`   SLC mined: ${totalSlcMined}`);
  console.log(`   Gas spent: ${totalGasSpent.toFixed(6)} ETH`);
  console.log(`   Wallet SLC: ${balance}`);
  console.log(`   Wallet ETH: ${formatEther(ethBalance)}`);
}

// Run
mine().catch(console.error);
