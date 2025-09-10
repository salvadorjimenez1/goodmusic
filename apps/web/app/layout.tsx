import "./globals.css"
import type { Metadata } from "next"
import Navbar from "../components/ui/Navbar"
import { MusicProvider } from "../context/MusicContext"

export const metadata: Metadata = {
  title: "GoodMusic 🎶",
  description: "A Goodreads-style app for music lovers",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-800 text-gray-900">
        <MusicProvider>
        <Navbar />
        <main className="max-w-4xl mx-auto p-4">{children}</main>
        </MusicProvider>
      </body>
    </html>
  )
}