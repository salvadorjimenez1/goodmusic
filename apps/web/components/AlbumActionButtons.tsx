"use client"

import Link from "next/link"
import { useState } from "react"
import { useMusic } from "../context/MusicContext"

interface Props {
  albumId: string
}

export default function AlbumActionButtons({ 
  albumId,
  title,
  artist,
}: {
  albumId: string
  title: string
  artist: string
}) {
  const {wantToListen, listened, addToWantToListen, addToListened, removeFromWantToListen, removeFromListened, removeAlbum} = useMusic()

  const isInWantToListen = wantToListen.some((a) => a.id === albumId)
  const isInListened = listened.some((a) => a.id === albumId)

  return (
    <div className="flex gap-4 mt-4" style={{paddingBottom: '25px'}}>
      <button
      className= {`px-4 py-2 rounded-lg border ${
        isInWantToListen
        ? "bg-yellow-500 text-white"
        : "text-white hover:bg-yellow-500 hover-text-white transition"
      }`}

        onClick={() => {
          if (isInWantToListen) {
            removeFromWantToListen(albumId);
          } else {
            addToWantToListen({ id: albumId, title, artist });
            removeFromListened(albumId);
          }
        }}
      >
        Want to listen
      </button>

       <button
       className={`px-4 py-2 rounded-lg border ${
          isInListened
          ? "bg-green-500 text-white"
          : "text-white hover:bg-green-500"
        }`}
        onClick={() => {
          if(isInListened) {
            removeFromListened(albumId);
          } else {
            addToListened({ id: albumId, title, artist })
            removeFromWantToListen(albumId);
          }
        }}
      >
        Listened
      </button>

    </div>
  )
}