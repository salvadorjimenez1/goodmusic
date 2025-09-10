"use client"

import { useState } from "react"
import AlbumCard from "../../components/AlbumCard"
import SearchBar from "../../components/SearchBar"

const dummyAlbums = [
  {
    id: "blonde",
    title: "Blonde",
    artist: "Frank Ocean",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/a/a0/Blonde_-_Frank_Ocean.jpeg",
  },
  {
    id: "damn",
    title: "DAMN.",
    artist: "Kendrick Lamar",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/5/51/Kendrick_Lamar_-_Damn.png",
  },
  {
    id: "tpab",
    title: "To Pimp a Butterfly",
    artist: "Kendrick Lamar",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/f/f6/Kendrick_Lamar_-_To_Pimp_a_Butterfly.png",
  },
  {
    id: "currents",
    title: "Currents",
    artist: "Tame Impala",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/9/9b/Tame_Impala_-_Currents.png",
  },
]

export default function SearchPage() {
  const [results, setResults] = useState(dummyAlbums)

  const handleSearch = (query: string) => {
    const filtered = dummyAlbums.filter(
      (album) =>
        album.title.toLowerCase().includes(query.toLowerCase()) ||
        album.artist.toLowerCase().includes(query.toLowerCase())
    )
    setResults(filtered)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4  text-white">Search Albums 🔍</h2>
      <SearchBar onSearch={handleSearch} />

      {results.length === 0 ? (
        <p className=" text-white">No results found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {results.map((album) => (
            <AlbumCard key={album.id} {...album} />
          ))}
        </div>
      )}
    </div>
  )
}