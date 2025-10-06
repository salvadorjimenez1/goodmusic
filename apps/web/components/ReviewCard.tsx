import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { Star } from "lucide-react";
import Link from "next/link";

interface Props {
  username: string;
  rating: number | null;
  comment: string;
  spotify_album_id: string;
  created_at: string;
  updated_at?: string | null;
  context?: "album" | "profile";
}

export default function ReviewCard({ username, rating, comment, spotify_album_id, created_at, updated_at, context = "profile"}: Props) {
  const [album, setAlbum] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await apiFetch(`/spotify/albums/${spotify_album_id}`);
        setAlbum(data);
      } catch (err) {
        console.error("Failed to fetch album info", err);
      }
    })();
  }, [spotify_album_id]);

  function renderStars(rating: number) {
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
        stars.push(<Star key={i} className="w-4 h-4 text-gray-300 inline-block" />);
      }
    }
    return stars;
  }

  return (
   <div className="bg-gray-800 p-4 rounded-lg shadow-md text-white flex gap-4">
      {context === "profile" && album && (
        <Link href={`/album/${spotify_album_id}`}>
          <img
            src={album.images?.[0]?.url ?? "/placeholder.png"}
            alt={`${album.name} cover`}
            className="w-16 h-16 rounded hover:opacity-80 transition"
          />
        </Link>
      )}

      <div className="flex-1">
        {context === "album" ? (
        <h3 className="text-lg font-semibold">
          <Link
            href={`/profile/${username}`}
            className="text-indigo-300 hover:underline hover:text-indigo-400"
          >
            {username}
          </Link>{" "}
          <span className="text-gray-400">reviewed this album</span>
        </h3>
      ) : (
          <h3 className="text-lg font-semibold">
            <Link
              href={`/album/${spotify_album_id}`}
              className="hover:underline hover:text-indigo-400"
            >
              {album ? album.name : "Loading..."}
            </Link>{" "}
            <span className="text-gray-400">— {album?.artists?.[0]?.name}</span>
          </h3>
        )}

        {/* Rating + date */}
          {rating ? <span className="flex">{renderStars(rating)}</span> : <span>No rating</span>}
          <span>
            {new Date(created_at).toLocaleDateString()}
            {updated_at && updated_at !== created_at && (
              <span className="italic text-gray-500 ml-1">
                (edited {new Date(updated_at).toLocaleDateString()})
              </span>
            )}
          </span>

        {/* Review text */}
        <p className="text-gray-200">{comment}</p>
      </div>
    </div>
  );
}