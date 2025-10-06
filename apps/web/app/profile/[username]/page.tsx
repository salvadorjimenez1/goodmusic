"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "../../../context/AuthContext";
import { apiFetch } from "../../../lib/api";
import AlbumCard from "../../../components/AlbumCard";
import ReviewCard from "../../../components/ReviewCard";

type SpotifyAlbum = {
  id: string;
  name: string;
  artists: { name: string }[];
  images: { url: string }[];
};

export default function ProfilePage() {
  const params = useParams();
  const username = params.username as string;

  const { user: loggedInUser } = useAuth();
  const [profileUser, setProfileUser] = useState<any>(null);
  const [albums, setAlbums] = useState<any[]>([]);
  const [reviews, setReviews] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"want" | "listened" | "favorites" | "reviews">("want");

  const isOwnProfile = loggedInUser?.username === profileUser?.username;

  // Load profile by username
  useEffect(() => {
    (async () => {
      try {
        const data = await apiFetch(`/users/by-username/${username}`);
        setProfileUser(data);
      } catch (err) {
        console.error("Failed to fetch profile", err);
        setProfileUser(null);
      }
    })();
  }, [username]);

  // Load statuses for this profile
  useEffect(() => {
    if (!profileUser) return;

    (async () => {
      try {
        const res = await apiFetch(`/users/${profileUser.id}/statuses`);
        const statusesData = res.items || []; // ✅ use .items

        const enriched = await Promise.all(
          statusesData.map(async (s: any) => {
            try {
              const album: SpotifyAlbum = await apiFetch(`/spotify/albums/${s.spotify_album_id}`);
              return {
                id: album.id,
                title: album.name,
                artist: album.artists?.[0]?.name ?? "Unknown Artist",
                coverUrl: album.images?.[0]?.url ?? "/placeholder.png",
                status: s.status,
                is_favorite: s.is_favorite ?? false,
              };
            } catch {
              return {
                id: s.spotify_album_id,
                title: "Unknown Album",
                artist: "Unknown Artist",
                coverUrl: "/placeholder.png",
                status: s.status,
                is_favorite: s.is_favorite ?? false,
              };
            }
          })
        );
        setAlbums(enriched);
      } catch (err) {
        console.error("Failed to fetch statuses", err);
        setAlbums([]);
      }
    })();
  }, [profileUser]);

  // Load reviews for this profile
  useEffect(() => {
    if (activeTab === "reviews" && profileUser) {
      (async () => {
        try {
          const data = await apiFetch(`/users/${profileUser.id}/reviews?limit=50&offset=0`);
          setReviews(data.items || []);
        } catch (err) {
          console.error("Failed to fetch reviews", err);
          setReviews([]);
        }
      })();
    }
  }, [activeTab, profileUser]);

  if (!profileUser) {
    return <p className="text-white">Loading profile...</p>;
  }

  // Filter albums by tab (match backend enum values)
  const filteredAlbums = albums.filter((a) => {
    if (activeTab === "want") return a.status === "want-to-listen";
    if (activeTab === "listened") return a.status === "listened";
    if (activeTab === "favorites") return a.is_favorite;
    return false;
  });

  return (
    <div className="max-w-4xl mx-auto mt-8 text-white">
      <h1 className="text-3xl font-bold mb-6">
        {isOwnProfile ? "My Music Shelf" : `${profileUser.username}’s Music Shelf`}
      </h1>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-700 mb-6">
        <button
          className={`pb-2 ${activeTab === "want" ? "border-b-2 border-indigo-500 text-indigo-400" : "text-gray-400"}`}
          onClick={() => setActiveTab("want")}
        >
          Want to Listen
        </button>
        <button
          className={`pb-2 ${activeTab === "listened" ? "border-b-2 border-indigo-500 text-indigo-400" : "text-gray-400"}`}
          onClick={() => setActiveTab("listened")}
        >
          Listened
        </button>
        <button
          className={`pb-2 ${activeTab === "favorites" ? "border-b-2 border-indigo-500 text-indigo-400" : "text-gray-400"}`}
          onClick={() => setActiveTab("favorites")}
        >
          Favorites
        </button>
        <button
          className={`pb-2 ${activeTab === "reviews" ? "border-b-2 border-indigo-500 text-indigo-400" : "text-gray-400"}`}
          onClick={() => setActiveTab("reviews")}
        >
          Reviews
        </button>
      </div>

      {/* Content */}
      {activeTab === "reviews" ? (
        <div className="space-y-4">
          {reviews.length > 0 ? (
            reviews.map((r) => (
              <ReviewCard
                key={r.id}
                username={r.user.username}
                rating={r.rating}
                comment={r.content}
                spotify_album_id={r.spotify_album_id}
                created_at={r.created_at}
                context="profile"
              />
            ))
          ) : (
            <p className="text-gray-400">No reviews yet.</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {filteredAlbums.length > 0 ? (
            filteredAlbums.map((a) => (
              <AlbumCard
                key={a.id}
                id={a.id}
                title={a.title}
                artist={a.artist}
                coverUrl={a.coverUrl}
              />
            ))
          ) : (
            <p className="text-gray-400">No albums in this category yet.</p>
          )}
        </div>
      )}
    </div>
  );
}