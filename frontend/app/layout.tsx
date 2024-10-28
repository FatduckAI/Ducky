import Navbar from "@/components/Navbar";
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Ducky's Brain",
  description: "Ducky's Stream of Thought by Fatduck AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body className="bg-ducky-bg font-mono">
        <Providers>
          <Navbar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
