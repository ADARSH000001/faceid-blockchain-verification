# Face ID + Blockchain Verification

Pipeline: **face scan → web reverse-image search → blockchain record & re-verification.**

## Operating Rule — Consent is Non-Negotiable

**This tool must only ever be run against your own face / your own publicly-posted
photos.** Do not run it against photos of other people. Reverse-image searching
someone else's face without their knowledge or consent may be illegal and is
ethically unacceptable regardless of legality. The authors bear no responsibility
for misuse.

## What it does

1. **Face detection & encoding** (`scripts/face_encode.py`) — detects a face in an
   input photo and produces a 128-dimension encoding using `face_recognition` (dlib).
2. **Web reverse-image search** (`scripts/find_match.py`) — sends the query photo
   to the **Google Cloud Vision API** (`web_detection` feature) and retrieves the
   best matching page URL from the public web. The API checks
   `pagesWithMatchingImages`, `fullMatchingImages`, and `partialMatchingImages`
   and returns the top result. No local candidate folder is involved; all matching
   happens inside Google's Vision infrastructure against publicly-indexed content.
3. **Blockchain verification** (`scripts/chain_verify.py`) — hashes the match
   record (SHA-256), writes it to a `ProofOfMatch` smart contract on Sepolia
   testnet, then reads the record back on-chain to prove it's tamper-evident.
4. **`scripts/pipeline.py`** runs all three steps end to end.

## Blockchain used

Ethereum **Sepolia testnet**. Contract: `contracts/ProofOfMatch.sol` — stores
`hash -> timestamp` and exposes `verifyRecord(hash)` for anyone to re-check
the record hasn't changed.

## How to run

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Cloud credentials (required for Step 2):**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create or select a GCP project.
   - Enable the **Cloud Vision API** for that project
     (*APIs & Services → Library → Cloud Vision API → Enable*).
   - Create a **service account** with the **Cloud Vision API User** role
     (*IAM & Admin → Service Accounts → Create → grant role*).
   - Download the service-account JSON key and save it somewhere on your machine.

3. **Deploy the smart contract:**
   Deploy `contracts/ProofOfMatch.sol` to Sepolia (e.g. via
   [Remix](https://remix.ethereum.org) connected to a MetaMask testnet wallet).
   Copy the deployed address.

4. **Get testnet ETH and an RPC URL:**
   Use an Alchemy or Infura free-tier endpoint for Sepolia, and fund the wallet
   from a Sepolia faucet.

5. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in all four variables:
   ```
   RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   PRIVATE_KEY=your_testnet_wallet_private_key_never_mainnet
   CONTRACT_ADDRESS=0xYourDeployedProofOfMatchAddress
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json
   ```

6. **Run the pipeline** (only the query photo is required — no candidates folder):
   ```bash
   python scripts/pipeline.py path/to/query_photo.jpg
   ```

## Known limitations

- **Vision API web-detection results depend on public indexing.** The search
  genuinely queries the public web via Google's Vision infrastructure — it is not
  local and not hardcoded. However, it can only find images that are already
  discoverable online. If the photo has never been posted publicly, or has not yet
  been indexed by Google, the API will return no match rather than inventing one.
  This is expected behavior, not a bug.
- **The blockchain step proves integrity, not correctness.** Writing a hash
  on-chain proves that specific hash existed at a given block time and hasn't
  been altered since. It does **not** independently verify that the underlying
  face match is accurate — a wrong match would be hashed and "verified" with
  equal confidence. Treat the on-chain record as a tamper-evident log of the
  match result, not a certification of the match's correctness.
- No retry/backoff logic on RPC calls — testnets can be flaky, particularly
  around faucet rate limits.
