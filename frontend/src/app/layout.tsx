import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "EU DPP Platform",
  description: "Digital Product Passport - EU compliance dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col">
            <header className="border-b border-slate-700 px-6 py-3 flex items-center gap-4">
              <h1 className="text-lg font-semibold">EU Digital Product Passport Platform</h1>
              <span className="ml-auto text-xs text-slate-500">ESPR · Battery Reg 2023/1542 · EU AI Act 2024/1689</span>
            </header>
            <main className="flex-1 p-6 overflow-auto">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
