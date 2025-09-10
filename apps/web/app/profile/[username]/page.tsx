"use client"

import Link from "next/link"
import { useState } from "react"
import { useMusic } from "../../../context/MusicContext"

export default function ProfilePage() {
  const { wantToListen, listened } = useMusic()
  const [activeTab, setActiveTab] = useState<"want" | "listened">("want")

  const albums =
    activeTab === "want" ? wantToListen : listened

  return (
    <div className="max-w-3xl mx-auto p-6 text-white">
      {/* Header */}
      <h1 className="text-2xl font-bold mb-4"> My Music Shelf </h1>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setActiveTab("want")}
          className={`px-4 py-2 rounded-lg ${
            activeTab === "want"
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700"
          }`}
        >
          Want to Listen
        </button>
        <button
          onClick={() => setActiveTab("listened")}
          className={`px-4 py-2 rounded-lg ${
            activeTab === "listened"
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700"
          }`}
        >
          Listened
        </button>
      </div>

      {/* Album List */}
      <div className="space-y-3">
        {albums.length > 0 ? (
          albums.map((album) => (
            <Link
              key={album.id}
              href={`/album/${album.id}`}
              className="block border p-4 rounded-lg hover:bg-slate-400"
            >
              <h2 className="text-lg font-semibold">{album.title}</h2>
              <p className="text-sm text-stone-300">{album.artist}</p>
            </Link>
          ))
        ) : (
          <p className="text-gray-500">No albums here yet.</p>
        )}
      </div>
    </div>
  )
}