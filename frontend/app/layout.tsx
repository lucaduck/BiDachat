import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "BIDACHAT · BI-DATA",
    template: "%s | BIDACHAT",
  },
  description:
    "Administra chatbots, fuentes de conocimiento y métricas para los cuadros de mando de BI-DATA.",
  robots: { index: false, follow: false },
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
