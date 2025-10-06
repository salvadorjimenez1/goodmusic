"use client"

import Link from "next/link";
import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { apiFetch } from "../lib/api";

interface AlbumCardProps {
  id: string;
  title: string;
  artist: string;
  coverUrl: string;
}

export default function AlbumCard({ id, title, artist, coverUrl }: AlbumCardProps) {
  const [avgRating, setAvgRating] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await apiFetch(`/albums/${id}/average-rating`);
        setAvgRating(data.average);
      } catch (err) {
        console.error("Failed to fetch avg rating", err);
      }
    })();
  }, [id]);

  const renderStars = (rating: number) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      if (rating >= i) {
        stars.push(<Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400 inline-block" />);
      } else if (rating >= i - 0.5) {
        stars.push(
          <span key={i} className="relative inline-block w-4 h-4">
            <Star className="absolute w-4 h-4 text-gray-300" />
            <div className="absolute top-0 left-0 w-1/2 overflow-hidden">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
            </div>
          </span>
        );
      } else {
        stars.push(<Star key={i} className="w-4 h-4 text-gray-500 inline-block" />);
      }
    }
    return stars;
  };

  return (
    <Link href={`/album/${id}`}>
      <div className="relative rounded-lg overflow-hidden shadow-md cursor-pointer group">
        <img
          src={coverUrl}
          alt={`${title} cover`}
          className="w-full h-64 object-cover transition-transform duration-300 group-hover:scale-105"
        />

        <div className="absolute inset-0 bg-gray-500 bg-opacity-60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-center p-2">
          <h3 className="text-white font-semibold text-lg">{title}</h3>
          <p className="text-gray-300 text-md mb-2">{artist}</p>
          {avgRating !== null ? (
            <div className="flex">{renderStars(avgRating)}</div>
          ) : (
            <p className="text-gray-300 text-xs">No ratings</p>
          )}
        </div>
      </div>
    </Link>
  );
}