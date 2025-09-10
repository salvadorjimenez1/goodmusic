"use client"

import { useState } from "react"
import ReviewCard from "./ReviewCard"

interface Props {
  albumId: string
}

export default function ReviewSection({ albumId }: Props) {
  const [reviews, setReviews] = useState([
    { username: "Alice", rating: 5, comment: "Absolutely love this album!" },
    { username: "Bob", rating: 4, comment: "Great tracks but a bit long." },
  ])
  const [newComment, setNewComment] = useState("")
  const [newRating, setNewRating] = useState(5)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setReviews([{ username: "DemoUser", rating: newRating, comment: newComment }, ...reviews])
    setNewComment("")
    setNewRating(5)
  }

  return (
    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4 text-white">Reviews</h3>

      {/* Review Form */}
      <form onSubmit={handleSubmit} className="mb-6 space-y-3">
        <div>
          <label className="block mb-1 font-medium text-white">Rating</label>
          <select
            value={newRating}
            onChange={(e) => setNewRating(Number(e.target.value))}
            className="px-2 py-1 border rounded bg-white"
          >
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>
                {n} Star{n > 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block mb-1 font-medium text-white">Comment</label>
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            rows={3}
            className="bg-white w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Write your review..."
          />
        </div>

        <button
          type="submit"
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-500 transition"
        >
          Submit Review
        </button>
      </form>

      {/* Reviews List */}
      {reviews.length === 0 ? (
        <p className="text-gray-500">No reviews yet.</p>
      ) : (
        reviews.map((rev, i) => <ReviewCard key={i} {...rev} />)
      )}
    </div>
  )
}