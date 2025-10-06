"use client";

import { use, useEffect, useState } from "react";
import Image from "next/image";
import { Star } from "lucide-react";
import ReviewSection from "../../../components/ReviewSelection";
import AlbumActionButtons from "../../../components/AlbumActionButtons";
import { apiFetch } from "../../../lib/api";

type SpotifyAlbum = {
  id: string;
  name: string;
  images: { url: string }[];
  release_date?: string;
  artists: { id: string; name: string }[];
  tracks?: { items: { id: string; name: string }[] };
};

type UiAlbum = {
  id: string;
  title: string;
  artists: string[];
  coverUrl: string;
  tracks: string[];
  releaseDate?: string;
};

function renderStars(rating: number) {
  const stars = [];
  for (let i = 1; i <= 5; i++) {
    if (rating >= i) {
      stars.push(<Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400 inline-block" />);
    } else if (rating >= i - 0.5) {
      stars.push(
        <span key={i} className="relative inline-block w-5 h-5">
          <Star className="absolute w-5 h-5 text-gray-300" />
          <div className="absolute top-0 left-0 w-1/2 overflow-hidden">
            <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
          </div>
        </span>
      );
    } else {
      stars.push(<Star key={i} className="w-5 h-5 text-gray-500 inline-block" />);
    }
  }
  return stars;
}

function formatDate(dateStr: string) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function AlbumDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params); // ✅ unwrap the promise

  const [album, setAlbum] = useState<UiAlbum | null>(null);
  const [avgRating, setAvgRating] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        // fetch album from backend
        const res = await fetch(`http://localhost:8000/spotify/albums/${id}`, { cache: "no-store" });
        if (!res.ok) return;
        const data: SpotifyAlbum = await res.json();
        setAlbum({
          id: data.id,
          title: data.name,
          artists: data.artists?.map((a) => a.name) ?? ["Unknown Artist"],
          coverUrl: data.images?.[0]?.url ?? "/placeholder.png",
          tracks: data.tracks?.items?.map((t) => t.name) ?? [],
          releaseDate: data.release_date,
        });

        // fetch average rating
        const ratingData = await apiFetch(`/albums/${id}/average-rating`);
        setAvgRating(ratingData.average);
      } catch (err) {
        console.error("Error loading album", err);
      }
    })();
  }, [id]);

  if (!album) return <p className="text-red-500">Album not found</p>;

  return (
    <div className="text-white">
      <div className="flex flex-col md:flex-row gap-6 mb-8">
        <Image
          src={album.coverUrl}
          alt={`${album.title} cover`}
          width={300}
          height={300}
          className="rounded-lg shadow-md"
        />
        <div>
          <h1 className="text-3xl font-bold">{album.title}</h1>
          <h2 className="text-xl text-gray-400 mb-2">{album.artists.join(", ")}</h2>
          {album.releaseDate && (
            <p className="text-sm text-gray-400">Released: {formatDate(album.releaseDate)}</p>
          )}

          {/* Average Rating */}
          {avgRating !== null ? (
            <div className="flex items-center gap-2 mt-2">
              <span className="flex">{renderStars(avgRating)}</span>
              <span className="text-gray-300 text-sm">({avgRating} average)</span>
            </div>
          ) : (
            <p className="text-gray-500 text-sm mt-2">No ratings yet</p>
          )}
        </div>
      </div>

      <AlbumActionButtons
        albumId={album.id}
        title={album.title}
        artist={album.artists.join(", ")}
      />

      {album.tracks.length > 0 && (
        <>
          <h3 className="text-xl font-semibold mb-4 mt-6">Tracklist</h3>
          <ol className="list-decimal pl-6 space-y-1 mb-6">
            {album.tracks.map((track, i) => (
              <li key={i}>{track}</li>
            ))}
          </ol>
        </>
      )}

      <ReviewSection albumId={album.id} />
    </div>
  );
}