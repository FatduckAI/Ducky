import {
  createAssociatedTokenAccountInstruction,
  createTransferCheckedInstruction,
  getAccount,
  getAssociatedTokenAddress,
} from "@solana/spl-token";
import {
  Connection,
  PublicKey,
  Transaction,
  type TransactionConfirmationStrategy,
} from "@solana/web3.js";
import type { Turnkey } from "@turnkey/sdk-server";
import { TurnkeySigner } from "@turnkey/solana";

export class DuckAiTokenAirdrop {
  private connection: Connection;
  private turnkeySigner: TurnkeySigner;
  private fromAddress: string;
  private mintAddress: string;

  constructor(
    turnkeyClient: Turnkey,
    fromAddress: string,
    mintAddress: string,
    rpcUrl: string = "https://api.devnet.solana.com"
  ) {
    this.connection = new Connection(rpcUrl, "confirmed");
    this.turnkeySigner = new TurnkeySigner({
      organizationId: turnkeyClient.config.defaultOrganizationId,
      client: turnkeyClient.apiClient(),
    });
    this.fromAddress = fromAddress;
    this.mintAddress = mintAddress;
  }

  private async getLatestBlockhashAndConfirmStrategy(
    signature: string
  ): Promise<{
    blockhash: string;
    confirmationStrategy: TransactionConfirmationStrategy;
  }> {
    const { blockhash, lastValidBlockHeight } =
      await this.connection.getLatestBlockhash();
    return {
      blockhash,
      confirmationStrategy: {
        signature,
        blockhash,
        lastValidBlockHeight,
      },
    };
  }

  async createAssociatedTokenAccountIfNeeded(
    recipientAddress: string
  ): Promise<PublicKey> {
    const fromKey = new PublicKey(this.fromAddress);
    const recipientKey = new PublicKey(recipientAddress);
    const mintKey = new PublicKey(this.mintAddress);

    // Get the associated token account address for the recipient
    const recipientAta = await getAssociatedTokenAddress(mintKey, recipientKey);

    // Check if the account already exists
    try {
      await getAccount(this.connection, recipientAta);
      return recipientAta;
    } catch (error) {
      // Account doesn't exist, create it
      const createAtaIx = createAssociatedTokenAccountInstruction(
        fromKey, // payer
        recipientAta, // ata
        recipientKey, // owner
        mintKey // mint
      );

      const transaction = new Transaction();
      transaction.add(createAtaIx);

      const { blockhash, confirmationStrategy } =
        await this.getLatestBlockhashAndConfirmStrategy(
          transaction.signature?.toString() ?? ""
        );

      transaction.recentBlockhash = blockhash;
      transaction.feePayer = fromKey;

      await this.turnkeySigner.addSignature(transaction, this.fromAddress);
      const txSignature = await this.connection.sendRawTransaction(
        transaction.serialize()
      );

      // Wait for confirmation using the new method
      await this.connection.confirmTransaction(confirmationStrategy);

      return recipientAta;
    }
  }

  async airdropTokens(
    recipientAddress: string,
    amount: number,
    decimals: number = 8
  ): Promise<string> {
    const fromKey = new PublicKey(this.fromAddress);
    const mintKey = new PublicKey(this.mintAddress);

    // Get sender's ATA
    const senderAta = await getAssociatedTokenAddress(mintKey, fromKey);

    // Get or create recipient's ATA
    const recipientAta = await this.createAssociatedTokenAccountIfNeeded(
      recipientAddress
    );

    // Create transfer instruction
    const transferIx = createTransferCheckedInstruction(
      senderAta, // from (should be a token account)
      mintKey, // mint
      recipientAta, // to (should be a token account)
      fromKey, // from's owner
      amount * Math.pow(10, decimals), // amount, scaled by decimals
      decimals // decimals
    );

    const transaction = new Transaction();
    transaction.add(transferIx);

    const { blockhash, confirmationStrategy } =
      await this.getLatestBlockhashAndConfirmStrategy(
        transaction.signature?.toString() ?? ""
      );

    transaction.recentBlockhash = blockhash;
    transaction.feePayer = fromKey;

    await this.turnkeySigner.addSignature(transaction, this.fromAddress);
    const txSignature = await this.connection.sendRawTransaction(
      transaction.serialize()
    );

    // Wait for confirmation using the new method
    await this.connection.confirmTransaction(confirmationStrategy);

    return txSignature;
  }

  async batchAirdrop(
    recipients: Array<{ address: string; amount: number }>,
    decimals: number = 8
  ): Promise<Array<{ address: string; signature: string }>> {
    const results = [];

    for (const recipient of recipients) {
      try {
        const signature = await this.airdropTokens(
          recipient.address,
          recipient.amount,
          decimals
        );
        results.push({
          address: recipient.address,
          signature: signature,
        });
        console.log(
          `Successfully airdropped ${recipient.amount} tokens to ${recipient.address}`
        );
        console.log(`Transaction signature: ${signature}`);
        console.log(
          `View on Explorer: https://explorer.solana.com/tx/${signature}`
        );
      } catch (error) {
        console.error(`Failed to airdrop to ${recipient.address}:`, error);
        results.push({
          address: recipient.address,
          signature: "failed",
        });
      }
    }

    return results;
  }

  async getTokenBalance(address: string): Promise<number> {
    const publicKey = new PublicKey(address);
    const mintKey = new PublicKey(this.mintAddress);

    const ata = await getAssociatedTokenAddress(mintKey, publicKey);

    try {
      const account = await getAccount(this.connection, ata);
      return Number(account.amount);
    } catch (error) {
      return 0;
    }
  }
}

// Example usage:
/*
const airdropper = new DuckAiTokenAirdrop(
  turnkeyClient,
  "YOUR_TURNKEY_WALLET_ADDRESS",
  "YOUR_DUCKAI_TOKEN_MINT_ADDRESS"
);

// Single airdrop
await airdropper.airdropTokens("RECIPIENT_ADDRESS", 100);

// Batch airdrop
const recipients = [
  { address: "ADDRESS1", amount: 100 },
  { address: "ADDRESS2", amount: 200 },
];
await airdropper.batchAirdrop(recipients);

// Check balance
const balance = await airdropper.getTokenBalance("ADDRESS");
*/
