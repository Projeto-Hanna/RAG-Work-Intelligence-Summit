import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "AgentLab | Work Intelligence Summit", description: "Crie, experimente e exporte seu agente de IA." };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
