import type { Metadata } from "next";
import "./globals.css";
import { VinciProvider } from "@/context/VinciContext";
import { ToastProvider } from "@/components/ui/Toast";

export const metadata: Metadata = {
  title: "Vinci — Fight Your Denial",
  description: "Vinci helps patients contest insurance prior authorization denials with evidence-backed appeal letters.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <VinciProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </VinciProvider>
      </body>
    </html>
  );
}
