import type { Metadata } from "next";
import Sidebar from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Project PUF — Public Healthcare Data",
  description: "Interactive platform for Medicare, Medicaid, and public healthcare data analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-slate-50 p-8">{children}</main>
      </body>
    </html>
  );
}
