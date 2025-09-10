"use client"

import { createContext, useContext, useState, ReactNode } from "react"

type Album = {
  id: string
  title: string
  artist: string
}

type MusicContextType = {
  wantToListen: Album[]
  listened: Album[]
  addToWantToListen: (album: Album) => void
  addToListened: (album: Album) => void
  removeFromWantToListen: (albumId: string) => void;
  removeFromListened: (albumId: string) => void;
  removeAlbum: (albumId: string) => void;
}

const MusicContext = createContext<MusicContextType | undefined>(undefined)

export function MusicProvider({ children }: { children: ReactNode }) {
  const [wantToListen, setWantToListen] = useState<Album[]>([])
  const [listened, setListened] = useState<Album[]>([])

  const addToWantToListen = (album: Album) => {
     // remove from listened if it's there
    setListened((prev) => prev.filter((a) => a.id !== album.id))
    // add if not already in wantToListen
    if (!wantToListen.find((a) => a.id === album.id)) {
      setWantToListen((prev) => [...prev, album])
    }
  }

  const addToListened = (album: Album) => {
    // remove from wantToListen if it's there
    setWantToListen((prev) => prev.filter((a) => a.id !== album.id))
    // add if not already in listened
    if (!listened.find((a) => a.id === album.id)) {
      setListened((prev) => [...prev, album])
    }
  }

  const removeFromWantToListen = (albumId: string) => {
    setWantToListen((prev) => prev.filter((a) => a.id !== albumId));
  };

  const removeFromListened = (albumId: string) => {
    setListened((prev) => prev.filter((a) => a.id !== albumId));
  };
  
  const removeAlbum = (albumId: string) => {
    setWantToListen((prev) => prev.filter((a) => a.id !== albumId));
    setListened((prev) => prev.filter((a) => a.id !== albumId));
}

  return (
    <MusicContext.Provider
      value={{ wantToListen, listened, addToWantToListen, addToListened, removeFromWantToListen, removeFromListened, removeAlbum}}
    >
      {children}
    </MusicContext.Provider>
  )
}

export function useMusic() {
  const context = useContext(MusicContext)
  if (!context) {
    throw new Error("useMusic must be used within a MusicProvider")
  }
  return context
}