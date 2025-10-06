"use client";

import { createContext, useContext, useState, ReactNode, useEffect } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "./AuthContext";

type Status = "listened" | "want-to-listen";

type UserAlbumStatus = {
  id: number;
  spotify_album_id: string;
  status: Status;
  is_favorite: boolean;
  created_at: string;
  user: { id: number; username: string };
};

type MusicContextType = {
  statuses: UserAlbumStatus[];
  addStatus: (albumId: string, status: Status, is_favorite?: boolean) => Promise<void>;
  updateStatus: (
    statusId: number,
    payload: { status: Status; is_favorite: boolean }
  ) => Promise<void>;
  removeStatus: (statusId: number) => Promise<void>;
};

const MusicContext = createContext<MusicContextType | undefined>(undefined);

export function MusicProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [statuses, setStatuses] = useState<UserAlbumStatus[]>([]);

  useEffect(() => {
    if (!user) return;
    (async () => {
      const data = await apiFetch(`/users/${user.id}/statuses`);
      setStatuses(data.items);
    })();
  }, [user]);

  async function addStatus(
    albumId: string,
    status: Status,
    is_favorite: boolean = false
  ) {
    if (!user) return;
    const newStatus: UserAlbumStatus = await apiFetch(`/statuses`, {
      method: "POST",
      body: JSON.stringify({
        user_id: user.id,
        spotify_album_id: albumId,
        status,
        is_favorite,
      }),
    });
    setStatuses((prev) => [...prev, newStatus]);
  }

  async function updateStatus(
    statusId: number,
    payload: { status: Status; is_favorite: boolean }
  ) {
    const updated: UserAlbumStatus = await apiFetch(`/statuses/${statusId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    setStatuses((prev) =>
      prev.map((s) => (s.id === statusId ? updated : s))
    );
  }

  async function removeStatus(statusId: number) {
    await apiFetch(`/statuses/${statusId}`, { method: "DELETE" });
    setStatuses((prev) => prev.filter((s) => s.id !== statusId));
  }

  return (
    <MusicContext.Provider value={{ statuses, addStatus, updateStatus, removeStatus }}>
      {children}
    </MusicContext.Provider>
  );
}

export function useMusic() {
  const ctx = useContext(MusicContext);
  if (!ctx) throw new Error("useMusic must be used within MusicProvider");
  return ctx;
}