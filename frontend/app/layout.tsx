import "./globals.css";
import type { ReactNode } from "react";

export const metadata = { title: "MedScribe", description: "Speech to structured clinical notes" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
