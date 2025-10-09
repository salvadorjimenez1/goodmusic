"use client"

import Link from "next/link"
import { useState } from "react"
import UserAvatar from "./UserAvatar"
import { apiFetch } from "../lib/api"
import { useAuth } from "@/context/AuthContext"

type UserCardProps = {
  id: number
  username: string
  profilePicture?: string | null
  isFollowing?: boolean
}

export default function UserCard({ id, username, profilePicture, isFollowing }: UserCardProps) {
  const [following, setFollowing] = useState(isFollowing ?? false)
  const { user: loggedInUser } = useAuth()

  const isOwnProfile = loggedInUser?.username === username

  const toggleFollow = async () => {
    try {
      const action = following ? "unfollow" : "follow"
      await apiFetch(`/users/${id}/${action}`, {
        method: following ? "DELETE" : "POST",
      })
      setFollowing(!following)
    } catch (err) {
      console.error("Failed to toggle follow", err)
    }
  }

  return (
    <li className="flex items-center gap-6 text-white py-4 border-b border-gray-700">
      <Link href={`/profile/${username}`} className="flex items-center gap-10 hover:underline text-xl">
        <UserAvatar username={username} profilePicture={profilePicture} size={60} />
        <span>{username}</span>
      </Link>
    </li>
  )
}