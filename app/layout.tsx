import type { Metadata } from "next";
import "./globals.css";
import { MepiaAuthProvider } from "@/components/auth/MepiaAuthProvider";
import { MepiaShell } from "@/components/layout/MepiaShell";
import GlassBackground from "@/components/GlassBackground";

export const metadata: Metadata = {
  title: "MEPIA — Copiloto Financiero",
  description: "Auditoría operativa y financiera para restaurantes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-canvas text-zinc-100 font-sans antialiased">
        <GlassBackground />
        <div className="page-content min-h-screen"><MepiaAuthProvider><MepiaShell>{children}</MepiaShell></MepiaAuthProvider></div>
      </body>
    </html>
  );
}
