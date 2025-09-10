import AlbumCard from "../components/AlbumCard"
import React from "react";
import Link from "next/link";

const dummyAlbums = [
  {
    id: "blonde",
    title: "Blonde",
    artist: "Frank Ocean",
    coverUrl:
      "https://upload.wikimedia.org/wikipedia/en/a/a0/Blonde_-_Frank_Ocean.jpeg",
  },
  {
    id: "damn",
    title: "DAMN.",
    artist: "Kendrick Lamar",
    coverUrl:
      "https://upload.wikimedia.org/wikipedia/en/5/51/Kendrick_Lamar_-_Damn.png",
  },
  {
    id: "tpab",
    title: "To Pimp a Butterfly",
    artist: "Kendrick Lamar",
    coverUrl:
      "https://upload.wikimedia.org/wikipedia/en/f/f6/Kendrick_Lamar_-_To_Pimp_a_Butterfly.png",
  },
  {
    id: "currents",
    title: "Currents",
    artist: "Tame Impala",
    coverUrl:
      "https://upload.wikimedia.org/wikipedia/en/9/9b/Tame_Impala_-_Currents.png",
  },
]

type Album = {
  id: number;
  title: string;
  artist: string;
};

async function getAlbums(): Promise<Album[]> {
  try {
    const res = await fetch("http://localhost:8000/albums", {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching albums:", err);
    return [];
  }
}

export default async function HomePage() {
  const albums = await getAlbums();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-white">Trending Albums 🎵</h2>

     <ul className="space-y-2">
      {albums.map((album) => (
        <li key={album.id} style={{paddingLeft: '15px'}} className="bg-white rounded-2xl shadow-md overflow-hidden hover:shadow-lg transition cursor-pointer">
        <Link className= "text-lg font-semibold" href={`/album/${album.id}`}>
            {album.title} <span className="text-gray-600">by {album.artist}</span>
        </Link>
        </li>
        ))}
      </ul>
    </div>
  )
}
  // return (
  //   <div className="p-6">
  //     <h1 className="text-xl font-bold mb-4">Albums</h1>

  //     <ul className="space-y-2">
  //       {albums.map((album) => (
  //         <li key={album.id} className="border p-2 rounded">
  //           <Link href={`/album/${album.id}`}>
  //             {album.title} <span className="text-gray-500">by {album.artist}</span>
  //           </Link>
  //         </li>
  //       ))}
  //     </ul>
  //   </div>
  // );