"""
Step 3 — Blockchain upload & verification.

Hashes the matched post's data (filename, path, and metadata you supply),
writes the hash to the ProofOfMatch contract on Sepolia testnet, then
re-reads it from-chain to prove the record is tamper-evident.

Requires environment variables (see .env.example):
    RPC_URL              - e.g. an Alchemy/Infura Sepolia HTTPS endpoint
    PRIVATE_KEY           - testnet wallet private key (NEVER a mainnet key)
    CONTRACT_ADDRESS      - deployed ProofOfMatch address
"""
import os
import hashlib
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

# Load .env from the project root (one level up from scripts/)
load_dotenv(Path(__file__).parent.parent / ".env")

CONTRACT_ABI = json.loads("""
[
  {"inputs":[{"internalType":"bytes32","name":"hash","type":"bytes32"}],
   "name":"storeRecord","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"hash","type":"bytes32"}],
   "name":"verifyRecord",
   "outputs":[{"internalType":"bool","name":"exists","type":"bool"},
              {"internalType":"uint256","name":"timestamp","type":"uint256"}],
   "stateMutability":"view","type":"function"}
]
""")


def hash_record(match_description: str) -> bytes:
    """Hash a text description of the match (e.g. filename + metadata)."""
    return hashlib.sha256(match_description.encode()).digest()


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {name}\n"
            f"Copy .env.example to .env and fill in your values."
        )
    return val


def store_and_verify(record_hash: bytes):
    rpc_url = _require_env("RPC_URL")
    private_key = _require_env("PRIVATE_KEY")
    contract_address = _require_env("CONTRACT_ADDRESS")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError("Could not connect to RPC endpoint. Check RPC_URL.")

    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=CONTRACT_ABI)

    print(f"Sending storeRecord tx from {account.address}...")
    tx = contract.functions.storeRecord(record_hash).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 100_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Tx sent: {tx_hash.hex()}. Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Confirmed in block {receipt.blockNumber}")

    exists, timestamp = contract.functions.verifyRecord(record_hash).call()
    print(f"Re-verified on-chain: exists={exists}, timestamp={timestamp}")
    return tx_hash.hex(), exists, timestamp


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python chain_verify.py "description of the matched post"')
        sys.exit(1)

    description = sys.argv[1]
    record_hash = hash_record(description)
    print(f"SHA-256 hash: {record_hash.hex()}")
    store_and_verify(record_hash)
