"use client"

import { useState } from "react"
import AlbumCard from "../../components/AlbumCard"
import SearchBar from "../../components/SearchBar"
import UserCard from "../../components/UserCard"
type SpotifyAlbum = {
  id: string;
  name: string;
  images: { url: string }[];
  artists: { name: string }[];
};

type UiAlbum = {
  id: string;
  title: string;
  artist: string;
  coverUrl: string;
};

type User = {
  id: number
  username: string
  profile_picture?: string
}


export default function SearchPage() {
  const [albums, setAlbums] = useState<UiAlbum[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [lastQuery, setLastQuery] = useState<string | null>(null)

  async function handleSearch(query: string) {
    try {
      setLastQuery(query)

      // Search albums
      const albumRes = await fetch(`http://localhost:8000/spotify/search?query=${encodeURIComponent(query)}`, { cache: "no-store" })
      const userRes = await fetch(`http://localhost:8000/users?q=${encodeURIComponent(query)}`, { cache: "no-store" })

      const albumData = albumRes.ok ? await albumRes.json() : null
      const userData = userRes.ok ? await userRes.json() : null

      const albumItems: SpotifyAlbum[] = albumData?.albums?.items ?? []
      const mappedAlbums = albumItems.map((a) => ({
        id: a.id,
        title: a.name,
        artist: a.artists?.[0]?.name ?? "Unknown Artist",
        coverUrl: a.images?.[0]?.url ?? "/placeholder.png",
      }))

      setAlbums(mappedAlbums)
      setUsers(userData?.items ?? [])
    } catch {
      setAlbums([])
      setUsers([])
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4 text-white">Search 🔍</h2>
      <SearchBar onSearch={handleSearch} />

      {lastQuery && (
        <div className="mt-6 mb-4 text-gray-400 text-sm border-b border-gray-700 pb-2 uppercase tracking-wide">
          Showing matches for “{lastQuery}”
        </div>
      )}

      {/* Users Section */}
      <ul className="space-y-4">
        {users.map((user) => (
          <UserCard
            key={user.id}
            id={user.id}
            username={user.username}
            profilePicture={user.profile_picture}
            // you can pass isFollowing if backend returns it
          />
        ))}
      </ul>
      
      {/* Albums Section */}
      <h3 className="text-xl font-semibold mt-6 mb-2 text-white"></h3>
      {albums.length === 0 ? (
        <p className="text-gray-400">No results found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {albums.map((album) => (
            <AlbumCard key={album.id} {...album} />
          ))}
        </div>
      )}
    </div>
  )
}