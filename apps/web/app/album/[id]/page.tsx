import Image from "next/image"
import ReviewSection from "../../../components/ReviewSelection"
import AlbumActionButtons from "../../../components/AlbumActionButtons"
import React from "react";

type Album = {
  id: number;
  title: string;
  coverUrl:string
  artist: string;
  tracks: string[]
}

async function getAlbums(id: string): Promise<Album | null> {
  try {
    const res = await fetch(`http://localhost:8000/albums/${id}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error("Error fetching album: ", err);
    return null;
  }
}

export default async function AlbumDetailPage({ params: { id } }: { params: { id: string } }) {
  const album = await getAlbums(id)

  if (!album) return <p className="text-red-500">Album not found</p>

  return (
    <div>
      {/* Album Info */}
      <div className="flex flex-col md:flex-row gap-6 mb-8 text-white">
        <Image
          src={album.coverUrl || "/placeholder.png" }
          alt={`${album.title} cover`}
          width={300}
          height={300}
          className="rounded-lg shadow-md"
        />
        <div>
          <h2 className="text-3xl font-bold">{album.title}</h2>
          <p className="text-lg text-gray-300">{album.artist}</p>
        </div>
      </div>

      {/* Album Action Buttons */}
      <AlbumActionButtons 
        albumId={id}
        title={album.title}
        artist={album.artist} 
      />

      {/* Tracklist
      <h3 className="text-xl font-semibold mb-4 text-white">Tracklist</h3>
      <ol className="list-decimal pl-6 space-y-1 mb-6 text-white">
        {album.tracks.map((track, i) => (
          <li key={i}>{track}</li>
        ))}
      </ol> */}

      {/* Reviews Section */}
      <ReviewSection albumId={id} />
    </div>
  )
}