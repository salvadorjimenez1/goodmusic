"use client"

import { useState, useEffect } from "react"
import ReviewCard from "./ReviewCard"
import { apiFetch } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Star } from "lucide-react";

interface Props {
  albumId: string
}

export default function ReviewSection({ albumId }: Props) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<any[]>([]);
  const [newComment, setNewComment] = useState("");
  const [newRating, setNewRating] = useState<number | null>(null);
  const [hoverRating, setHoverRating] = useState<number | null>(null);


  useEffect(() => {
    (async () => {
      const data = await apiFetch(`/reviews?spotify_album_id=${albumId}`);
      setReviews(data.items);
    })();
  }, [albumId]);

  if (!user) {
    return <p className="text-gray-400 mt-4">Login to review this album</p>;
  }

async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();
  if (!user) {
    alert("You must log in to post a review");
    return;
  }

  try {
    const newReview = await apiFetch(`/reviews`, {
      method: "POST",
      body: JSON.stringify({
        user_id: user.id,
        spotify_album_id: albumId,
        content: newComment,
        rating: newRating,
      }),
    });

    setReviews(prev =>
      prev.some(r => r.user.id === user.id && r.spotify_album_id === albumId)
        ? prev.map(r => 
            r.user.id === user.id && r.spotify_album_id === albumId ? newReview : r
          )
        : [newReview, ...prev]
    );

    setNewComment("");
    setNewRating(null);
  } catch (err) {
    console.error("Failed to post review:", err);
    alert("Error posting review");
  }
}

  // ---------- Star Rating Picker ----------
function StarRating({
  value,
  hoverValue,
  onChange,
  onHover,
}: {
  value: number | null;
  hoverValue: number | null;
  onChange: (val: number | null) => void;   // allow null now
  onHover: (val: number | null) => void;
}) {
  const activeValue = hoverValue ?? value ?? 0;
  const stars = [];

  for (let i = 1; i <= 5; i++) {
    const full = i <= activeValue;
    const half = !full && activeValue >= i - 0.5;

    stars.push(
      <div
        key={i}
        className="relative w-8 h-8 cursor-pointer"
        onMouseLeave={() => onHover(null)}
      >
        {/* base star outline */}
        <Star className="absolute inset-0 w-8 h-8 text-gray-300" />

        {/* full star fill */}
        {full && (
          <Star className="absolute inset-0 w-8 h-8 fill-yellow-400 text-yellow-400" />
        )}

        {/* half star fill */}
        {half && (
          <div className="absolute inset-0 w-1/2 overflow-hidden">
            <Star className="w-8 h-8 fill-yellow-400 text-yellow-400" />
          </div>
        )}

        {/* left half click area */}
        <div
          className="absolute inset-y-0 left-0 w-1/2"
          onMouseEnter={() => onHover(i - 0.5)}
          onClick={() => onChange(i - 0.5)}
        />

        {/* right half click area */}
        <div
          className="absolute inset-y-0 right-0 w-1/2"
          onMouseEnter={() => onHover(i)}
          onClick={() => onChange(i)}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-1">{stars}</div>

      {/* clear rating button */}
      {value !== null && (
        <button
          type="button"
          onClick={() => onChange(null)}
          className="text-sm text-red-500 hover:text-red-700 self-start"
        >
          Clear rating ✕
        </button>
      )}
    </div>
  );
}


  return (
    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4 text-white">Reviews</h3>

      <form onSubmit={handleSubmit} className="mb-6 space-y-3">
        <StarRating
          value={newRating}
          hoverValue={hoverRating}
          onChange={setNewRating}
          onHover={setHoverRating}
        />

        <textarea
          value={newComment}
          onChange={e => setNewComment(e.target.value)}
          rows={3}
          className="bg-white w-full px-3 py-2 border rounded text-gray-900"
          placeholder="Write your review..."
        />
        <button className="px-4 py-2 bg-indigo-600 text-white rounded">Submit</button>
      </form>
      {reviews.map(r => (
         <ReviewCard
          key={r.id}
          username={r.user.username}
          rating={r.rating}
          comment={r.content}
          spotify_album_id={r.spotify_album_id}
          created_at={r.created_at}
          updated_at={r.updated_at}
          context="album"
        />
      ))}
    </div>
  );
}