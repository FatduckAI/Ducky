import {
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createAssociatedTokenAccountInstruction,
  createInitializeMintInstruction,
  createMintToInstruction,
  getAssociatedTokenAddress,
  getMinimumBalanceForRentExemptMint,
  MINT_SIZE,
  TOKEN_PROGRAM_ID,
} from "@solana/spl-token";
import {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
  type TransactionConfirmationStrategy,
} from "@solana/web3.js";
import { Turnkey } from "@turnkey/sdk-server";
import { TurnkeySigner } from "@turnkey/solana";
import { ducky } from "../ducky/character";
import { turnkeyClient, validateEnvironment } from "./turnkeyClient";

class DevnetTokenManager {
  private connection: Connection;
  private turnkeySigner: TurnkeySigner;
  private fromAddress: string;
  private MIN_SOL_REQUIRED: number = 0.05;
  constructor(
    turnkeyClient: Turnkey,
    fromAddress: string,
    rpcUrl: string = "https://api.devnet.solana.com"
  ) {
    this.connection = new Connection(rpcUrl, "confirmed");
    this.turnkeySigner = new TurnkeySigner({
      organizationId: turnkeyClient.config.defaultOrganizationId,
      client: turnkeyClient.apiClient(),
    });
    this.fromAddress = fromAddress;
  }

  async checkDevnetBalance(): Promise<number> {
    const balance = await this.connection.getBalance(
      new PublicKey(this.fromAddress)
    );
    console.log(`Current devnet SOL balance: ${balance / 1e9} SOL`);
    return balance;
  }

  async requestDevnetAirdrop(): Promise<void> {
    // Get latest blockhash before airdrop
    const { blockhash, lastValidBlockHeight } =
      await this.connection.getLatestBlockhash("confirmed");

    const signature = await this.connection.requestAirdrop(
      new PublicKey(this.fromAddress),
      1_000_000_000 // 1 SOL
    );

    // Create confirmation strategy
    const confirmationStrategy: TransactionConfirmationStrategy = {
      signature,
      blockhash,
      lastValidBlockHeight,
    };

    // Wait for confirmation
    await this.connection.confirmTransaction(confirmationStrategy);
    console.log("Airdropped 1 devnet SOL");
  }

  private async tryRequestAirdrop(): Promise<boolean> {
    try {
      const { blockhash, lastValidBlockHeight } =
        await this.connection.getLatestBlockhash("confirmed");

      const signature = await this.connection.requestAirdrop(
        new PublicKey(this.fromAddress),
        1_000_000_000 // 1 SOL
      );

      const confirmationStrategy: TransactionConfirmationStrategy = {
        signature,
        blockhash,
        lastValidBlockHeight,
      };

      await this.connection.confirmTransaction(confirmationStrategy);
      console.log("Airdropped 1 devnet SOL");
      return true;
    } catch (error: any) {
      if (error.toString().includes("429 Too Many Requests")) {
        return false;
      }
      throw error;
    }
  }

  async ensureSufficientBalance(): Promise<boolean> {
    const balance = await this.checkDevnetBalance();
    const minRequired = this.MIN_SOL_REQUIRED * 1e9;

    if (balance >= minRequired) {
      return true;
    }

    const success = await this.tryRequestAirdrop();
    if (!success) {
      console.error(`
Unable to get devnet SOL via airdrop. Please try one of these alternatives:
1. Visit https://faucet.solana.com to request devnet SOL
2. Use solfaucet.com
3. Wait a few minutes and try again
4. Use a different wallet address

Current balance: ${balance / 1e9} SOL
Minimum required: ${this.MIN_SOL_REQUIRED} SOL
`);
      return false;
    }

    return true;
  }

  async createToken(
    tokenName: string,
    tokenSymbol: string,
    totalSupply: number = 1_000_000_000,
    decimals: number = 6
  ): Promise<{ mintAddress: string; supply: number }> {
    try {
      // Check balance and airdrop if needed
      const hasSufficientBalance = await this.ensureSufficientBalance();
      if (!hasSufficientBalance) {
        throw new Error("Insufficient SOL balance to create token");
      }

      // Create mint account
      const mintKeypair = Keypair.generate();
      const fromPubkey = new PublicKey(this.fromAddress);

      // Get rent-exempt amount
      const lamports = await getMinimumBalanceForRentExemptMint(
        this.connection
      );

      // Create account instruction
      const createAccountIx = SystemProgram.createAccount({
        fromPubkey,
        newAccountPubkey: mintKeypair.publicKey,
        space: MINT_SIZE,
        lamports,
        programId: TOKEN_PROGRAM_ID,
      });

      // Initialize mint instruction
      const initializeMintIx = createInitializeMintInstruction(
        mintKeypair.publicKey,
        decimals,
        fromPubkey,
        fromPubkey,
        TOKEN_PROGRAM_ID
      );

      // Get ATA address
      const ata = await getAssociatedTokenAddress(
        mintKeypair.publicKey,
        fromPubkey,
        false,
        TOKEN_PROGRAM_ID,
        ASSOCIATED_TOKEN_PROGRAM_ID
      );

      // Create ATA instruction
      const createAtaIx = createAssociatedTokenAccountInstruction(
        fromPubkey,
        ata,
        fromPubkey,
        mintKeypair.publicKey,
        TOKEN_PROGRAM_ID,
        ASSOCIATED_TOKEN_PROGRAM_ID
      );

      // Create mint to instruction
      const mintToIx = createMintToInstruction(
        mintKeypair.publicKey,
        ata,
        fromPubkey,
        totalSupply * Math.pow(10, decimals),
        [],
        TOKEN_PROGRAM_ID
      );

      // Get latest blockhash
      const { blockhash, lastValidBlockHeight } =
        await this.connection.getLatestBlockhash("confirmed");

      // Create and send first transaction (create and initialize mint)
      const tx1 = new Transaction().add(createAccountIx, initializeMintIx);
      tx1.feePayer = fromPubkey;
      tx1.recentBlockhash = blockhash;
      tx1.partialSign(mintKeypair);

      await this.turnkeySigner.addSignature(tx1, this.fromAddress);
      const sig1 = await this.connection.sendRawTransaction(tx1.serialize(), {
        skipPreflight: false,
        preflightCommitment: "confirmed",
      });

      // Create confirmation strategy
      const confirmationStrategy: TransactionConfirmationStrategy = {
        signature: sig1,
        blockhash: blockhash,
        lastValidBlockHeight: lastValidBlockHeight,
      };

      // Wait for confirmation
      await this.connection.confirmTransaction(confirmationStrategy);

      console.log("Token mint created");

      // Get new blockhash for second transaction
      const {
        blockhash: blockhash2,
        lastValidBlockHeight: lastValidBlockHeight2,
      } = await this.connection.getLatestBlockhash("confirmed");

      // Create and send second transaction (create ATA and mint tokens)
      const tx2 = new Transaction().add(createAtaIx, mintToIx);
      tx2.feePayer = fromPubkey;
      tx2.recentBlockhash = blockhash2;

      await this.turnkeySigner.addSignature(tx2, this.fromAddress);
      const sig2 = await this.connection.sendRawTransaction(tx2.serialize(), {
        skipPreflight: false,
        preflightCommitment: "confirmed",
      });

      // Create confirmation strategy for second transaction
      const confirmationStrategy2: TransactionConfirmationStrategy = {
        signature: sig2,
        blockhash: blockhash2,
        lastValidBlockHeight: lastValidBlockHeight2,
      };

      // Wait for confirmation of second transaction
      await this.connection.confirmTransaction(confirmationStrategy2);

      console.log(`
Token created successfully!
Mint Address: ${mintKeypair.publicKey.toString()}
Total Supply: ${totalSupply}
Decimals: ${decimals}
Explorer Link: https://explorer.solana.com/address/${mintKeypair.publicKey.toString()}?cluster=devnet
      `);

      return {
        mintAddress: mintKeypair.publicKey.toString(),
        supply: totalSupply,
      };
    } catch (error) {
      console.error("Error details:", error);
      throw error;
    }
  }
}

// Main execution function
async function main(testMode: boolean = false) {
  validateEnvironment();
  // You need to set these environment variables
  const DUCKY_WALLET_ADDRESS = testMode
    ? ducky.onchain.solanaDevnetAddress
    : ducky.onchain.solanaAddress;

  if (!DUCKY_WALLET_ADDRESS) {
    throw new Error("Please set DUCKY_WALLET_ADDRESS environment variable");
  }

  console.log("Creating token manager...");
  const tokenManager = new DevnetTokenManager(
    turnkeyClient,
    DUCKY_WALLET_ADDRESS
  );

  console.log("Creating new token...");
  const { mintAddress } = await tokenManager.createToken(
    "Token Devnet", // Token name
    "AI DEVNET", // Token symbol
    1_000_000_000, // 1 billion total supply
    6 // 6 decimals like USDC
  );

  console.log(`
✅ Setup complete!
Token mint address: ${mintAddress}
View on Explorer: https://explorer.solana.com/address/${mintAddress}?cluster=devnet
  `);

  // After this, you can use the DuckAiTokenAirdrop class to perform airdrops
  // using the mintAddress created above
}

// Run the script
main(true).catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
