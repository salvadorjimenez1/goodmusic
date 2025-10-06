"use client"

import { useState } from "react"
import AlbumCard from "../../components/AlbumCard"
import SearchBar from "../../components/SearchBar"
import { apiFetch } from "../../lib/api";

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


export default function SearchPage() {
  const [results, setResults] = useState<UiAlbum[]>([]);

  async function handleSearch(query: string) {
    try {
      const res = await fetch(`http://localhost:8000/spotify/search?query=${encodeURIComponent(query)}`, {
        cache: "no-store",
      });
      if (!res.ok) {
        setResults([]);
        return;
      }
      const data = await res.json();
      const items: SpotifyAlbum[] = data.albums?.items ?? [];

      const mapped = items.map((a) => ({
        id: a.id,
        title: a.name,
        artist: a.artists?.[0]?.name ?? "Unknown Artist",
        coverUrl: a.images?.[0]?.url ?? "/placeholder.png",
      }));
      setResults(mapped);
    } catch {
      setResults([]);
    }
  }

 return (
    <div>
      <h2 className="text-2xl font-bold mb-4 text-white">Search Albums 🔍</h2>
      <SearchBar onSearch={handleSearch} />

      {results.length === 0 ? (
        <p className="text-white">No results found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {results.map((album) => (
            <AlbumCard
              key={album.id}
              id={album.id}
              title={album.title}
              artist={album.artist}
              coverUrl={album.coverUrl}
            />
          ))}
        </div>
      )}
    </div>
  );
}