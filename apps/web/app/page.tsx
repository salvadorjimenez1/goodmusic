import AlbumCard from "../components/AlbumCard"
import React from "react";
import Link from "next/link";

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

async function getAlbums(query: string = "frank ocean"): Promise<UiAlbum[]> {
  try {
    const res = await fetch(`http://localhost:8000/spotify/search?query=${encodeURIComponent(query)}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    // Spotify search returns { albums: { items: [] } }
    const items: SpotifyAlbum[] = data.albums?.items ?? [];

    return items.map((a) => ({
      id: a.id,
      title: a.name,
      artist: a.artists?.[0]?.name ?? "Unknown Artist",
      coverUrl: a.images?.[0]?.url ?? "/placeholder.png",
    }));
  } catch {
    return [];
  }
}


export default async function HomePage() {
  const albums = await getAlbums();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-white">Trending Albums 🎵</h2>

      {albums.length === 0 ? (
        <p className="text-gray-400">No albums found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {albums.map((album) => (
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