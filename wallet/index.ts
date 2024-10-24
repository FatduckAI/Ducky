import SafeApiKit from "@safe-global/api-kit";
import Safe, { type PredictedSafeProps } from "@safe-global/protocol-kit";
import { type MetaTransactionData } from "@safe-global/safe-core-sdk-types";
import { TurnkeySigner } from "@turnkey/ethers";
import { Turnkey } from "@turnkey/sdk-server";
import { createAccount } from "@turnkey/viem";
import { ethers, JsonRpcProvider } from "ethers";

import {
  createPublicClient,
  createWalletClient,
  http,
  type Account,
  type PublicClient,
  type WalletClient,
} from "viem";
import { baseSepolia } from "viem/chains";

const baseSepoliaSafeAddress = "0xc268aad1Af67F9F8386c5F346f801B315D1B130E";

export class AISafeService {
  private turnkeyClient: Turnkey;
  private publicClient: PublicClient;
  private provider: JsonRpcProvider;

  constructor() {
    this.turnkeyClient = new Turnkey({
      apiBaseUrl: process.env.BASE_URL!,
      apiPrivateKey: process.env.API_PRIVATE_KEY!,
      apiPublicKey: process.env.API_PUBLIC_KEY!,
      defaultOrganizationId: process.env.ORGANIZATION_ID!,
    });

    // Initialize Viem public client
    this.publicClient = createPublicClient({
      chain: baseSepolia,
      transport: http(`https://rpc.ankr.com/base_sepolia`),
    });

    // Initialize Ethers provider
    this.provider = new ethers.JsonRpcProvider(
      `https://sepolia.infura.io/v3/${process.env.INFURA_KEY}`
    );
  }

  private async createWalletClient(account: Account): Promise<WalletClient> {
    return createWalletClient({
      account,
      chain: baseSepolia,
      transport: http(`https://sepolia.infura.io/v3/${process.env.INFURA_KEY}`),
    });
  }

  // Deploy a new Safe with 2/3 multisig configuration
  async deploySafe(
    aiWalletAddress: string,
    personalWalletAddress: string,
    backupWalletAddress: string,
    saltNonce?: string
  ) {
    // Create Turnkey account for AI signer
    const aiAccount = await createAccount({
      client: this.turnkeyClient.apiClient(),
      organizationId: process.env.ORGANIZATION_ID!,
      signWith: aiWalletAddress,
    });

    // Create wallet client
    const walletClient = await this.createWalletClient(aiAccount as Account);

    // Configure predicted Safe
    const predictedSafe: PredictedSafeProps = {
      safeAccountConfig: {
        owners: [aiWalletAddress, personalWalletAddress, backupWalletAddress],
        threshold: 2,
      },
      safeDeploymentConfig: {
        saltNonce: saltNonce || Date.now().toString(),
      },
    };

    // Initialize Safe SDK
    let protocolKit = await Safe.init({
      provider: `https://rpc.ankr.com/base_sepolia`,
      signer: process.env.AI_WALLET_ADDRESS!,
      predictedSafe,
    });

    // Get predicted address
    const safeAddress = await protocolKit.getAddress();
    console.log("Predicted Safe Address:", safeAddress);

    // Create deployment transaction
    const deploymentTransaction =
      await protocolKit.createSafeDeploymentTransaction();

    const client = await protocolKit.getSafeProvider().getExternalSigner();

    if (!client) {
      throw new Error("Failed to get external signer");
    }

    // Execute deployment transaction
    const txHash = await client.sendTransaction({
      account: aiAccount as Account,
      to: deploymentTransaction.to,
      value: BigInt(deploymentTransaction.value || 0),
      data: deploymentTransaction.data as `0x${string}`,
      chain: baseSepolia,
    });

    // Wait for deployment to complete
    const txReceipt = await this.publicClient.waitForTransactionReceipt({
      hash: txHash,
    });

    // Reconnect to the deployed Safe
    protocolKit = await protocolKit.connect({ safeAddress });

    // Verify deployment
    const isDeployed = await protocolKit.isSafeDeployed();
    if (!isDeployed) {
      throw new Error("Safe deployment failed");
    }

    // Return Safe details
    return {
      safeAddress: await protocolKit.getAddress(),
      owners: await protocolKit.getOwners(),
      threshold: await protocolKit.getThreshold(),
      deploymentTx: txHash,
    };
  }

  async sendTransaction() {
    const aiSigner = new TurnkeySigner({
      client: this.turnkeyClient.apiClient(),
      organizationId: process.env.ORGANIZATION_ID!,
      signWith: process.env.AI_WALLET_ADDRESS!,
    });

    const connectedSigner = aiSigner.connect(this.provider);
    const signerAddress = await connectedSigner.getAddress();

    console.log("Connected Signer Address:", signerAddress);

    // Initialize Safe API Kit
    const apiKit = new SafeApiKit({
      chainId: BigInt(84532),
    });

    // Initialize Safe v5 with Safe.init()
    const protocolKit = await Safe.init({
      provider: `https://base-sepolia.g.alchemy.com/v2/X_k0fXDiet6lKxJ-GtmhIIS8PpfMayar`,
      signer: signerAddress,
      safeAddress: baseSepoliaSafeAddress,
    });

    const owners = await protocolKit.getOwners();
    console.log("Safe Owners:", owners);

    if (!owners.includes(signerAddress)) {
      throw new Error(
        `Signer ${signerAddress} is not a Safe owner. Owners are: ${owners.join(
          ", "
        )}`
      );
    }

    const safeTransactionData: MetaTransactionData = {
      to: process.env.PERSONAL_WALLET_ADDRESS!,
      value: "100000000000000000",
      data: "0x",
    };

    const safeTransaction = await protocolKit.createTransaction({
      transactions: [safeTransactionData],
    });

    const safeTxHash = await protocolKit.getTransactionHash(safeTransaction);

    // Create EIP-712 typed data
    const domain = {
      chainId: 84532,
      verifyingContract: baseSepoliaSafeAddress,
    };

    const types = {
      SafeTx: [
        { name: "to", type: "address" },
        { name: "value", type: "uint256" },
        { name: "data", type: "bytes" },
        { name: "operation", type: "uint8" },
        { name: "safeTxGas", type: "uint256" },
        { name: "baseGas", type: "uint256" },
        { name: "gasPrice", type: "uint256" },
        { name: "gasToken", type: "address" },
        { name: "refundReceiver", type: "address" },
        { name: "nonce", type: "uint256" },
      ],
    };

    const safeTxData = {
      to: safeTransaction.data.to,
      value: safeTransaction.data.value,
      data: safeTransaction.data.data,
      operation: safeTransaction.data.operation,
      safeTxGas: safeTransaction.data.safeTxGas,
      baseGas: safeTransaction.data.baseGas,
      gasPrice: safeTransaction.data.gasPrice,
      gasToken: safeTransaction.data.gasToken,
      refundReceiver: safeTransaction.data.refundReceiver,
      nonce: safeTransaction.data.nonce,
    };

    // Sign using typed data
    const signature = await connectedSigner.signTypedData(
      domain,
      types,
      safeTxData
    );

    console.log("Safe Tx Hash:", safeTxHash);
    console.log("Signature:", signature);
    console.log("Sender Address for API:", signerAddress);

    try {
      const proposedTx = await apiKit.proposeTransaction({
        safeAddress: baseSepoliaSafeAddress,
        safeTransactionData: safeTransaction.data,
        safeTxHash,
        senderAddress: signerAddress,
        senderSignature: signature,
      });

      console.log("Successfully proposed transaction");
      return proposedTx;
    } catch (error) {
      console.error("Failed to propose transaction:", error);
      console.error("Safe address:", baseSepoliaSafeAddress);
      console.error("Sender address:", signerAddress);
      console.error(
        "Transaction data:",
        JSON.stringify(safeTransaction.data, null, 2)
      );
      throw error;
    }
  }
}
// Example usage
async function main() {
  const service = new AISafeService();

  try {
    // 1. Deploy new Safe
    /* const safeDetails = await service.deploySafe(
      process.env.AI_WALLET_ADDRESS!,
      process.env.PERSONAL_WALLET_ADDRESS!,
      process.env.BACKUP_WALLET_ADDRESS!
    );
    console.log("Deployed Safe:", safeDetails); */
    const txHash = await service.sendTransaction();
    console.log("Transaction Hash:", txHash);
  } catch (error) {
    console.error("Error:", error);
    throw error;
  }
}

main().catch(console.error);
