import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Razorpay Financial Intelligence",
  description: "Financial operations overview for Razorpay settlements and reconciliation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
