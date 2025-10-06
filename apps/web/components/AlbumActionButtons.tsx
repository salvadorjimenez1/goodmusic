"use client"

import Link from "next/link"
import { useState } from "react"
import { useMusic } from "../context/MusicContext"
import { useAuth } from "../context/AuthContext";

export default function AlbumActionButtons({
  albumId,
  title,
  artist,
}: {
  albumId: string;
  title: string;
  artist: string;
}) {
  const { statuses, addStatus, updateStatus, removeStatus } = useMusic();
  const { user } = useAuth();

  if (!user) {
    return <p className="text-gray-400 mt-4">Login to track this album</p>;
  }

  // Find if the current album already has a status for this user
  const current = statuses.find((s) => s.spotify_album_id === albumId);

  const isInWantToListen = current?.status === "want-to-listen";
  const isInListened = current?.status === "listened";
  const isFavorite = current?.is_favorite ?? false; // ✅ use is_favorite flag

  async function toggleWantToListen() {
    if (isInWantToListen && current) {
      await removeStatus(current.id);
    } else {
      if (current) await removeStatus(current.id);
      await addStatus(albumId, "want-to-listen");
    }
  }

  async function toggleListened() {
    if (isInListened && current) {
      await removeStatus(current.id);
    } else {
      if (current) await removeStatus(current.id);
      await addStatus(albumId, "listened");
    }
  }

  async function toggleFavorite() {
    if (!current) {
      // If no status exists yet, create with want-to-listen + favorite
      await addStatus(albumId, "want-to-listen", true);
    } else {
      // Flip favorite without changing the main status
      await updateStatus(current.id, {
        status: current.status,
        is_favorite: !isFavorite,
      });
    }
  }

  return (
    <div className="flex gap-4 mt-4" style={{ paddingBottom: "25px" }}>
      <button
        className={`px-4 py-2 rounded-lg border ${
          isInWantToListen
            ? "bg-yellow-500 text-white"
            : "text-white hover:bg-yellow-500 transition"
        }`}
        onClick={toggleWantToListen}
      >
        Want to Listen
      </button>

      <button
        className={`px-4 py-2 rounded-lg border ${
          isInListened
            ? "bg-green-500 text-white"
            : "text-white hover:bg-green-500 transition"
        }`}
        onClick={toggleListened}
      >
        Listened
      </button>

      <button
        className={`px-4 py-2 rounded-lg border ${
          isFavorite
            ? "bg-red-500 text-white"
            : "text-white hover:bg-red-500 transition"
        }`}
        onClick={toggleFavorite}
      >
        Favorite ❤️
      </button>
    </div>
  );
}