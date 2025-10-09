"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../../context/AuthContext";
import { apiFetch } from "../../../lib/api";
import AlbumCard from "../../../components/AlbumCard";
import ReviewCard from "../../../components/ReviewCard";
import Modal from "../../../components/Modal";
import UserAvatar from "../../../components/UserAvatar";

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
  const [followers, setFollowers] = useState<any[]>([]);
  const [following, setFollowing] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<
    "want" | "listened" | "favorites" | "reviews"
  >("want");

  const [showFollowersModal, setShowFollowersModal] = useState(false);
  const [showFollowingModal, setShowFollowingModal] = useState(false);
  const [showAvatarModal, setShowAvatarModal] = useState(false);

  const isOwnProfile = loggedInUser?.username === profileUser?.username;

  // Load profile by username (full detail)
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
        const statusesData = res.items || [];
        const enriched = await Promise.all(
          statusesData.map(async (s: any) => {
            try {
              const album: SpotifyAlbum = await apiFetch(
                `/spotify/albums/${s.spotify_album_id}`
              );
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

  // Load reviews when Reviews tab is active
  useEffect(() => {
    if (activeTab === "reviews" && profileUser) {
      (async () => {
        try {
          const data = await apiFetch(
            `/users/${profileUser.id}/reviews?limit=50&offset=0`
          );
          setReviews(data.items || []);
        } catch (err) {
          console.error("Failed to fetch reviews", err);
          setReviews([]);
        }
      })();
    }
  }, [activeTab, profileUser]);

  // Load followers/following
  useEffect(() => {
    if (showFollowersModal && profileUser) {
      (async () => {
        const res = await apiFetch(`/users/${profileUser.id}/followers`);
        setFollowers(res.users || []);
      })();
    }
  }, [showFollowersModal, profileUser]);

  useEffect(() => {
    if (showFollowingModal && profileUser) {
      (async () => {
        const res = await apiFetch(`/users/${profileUser.id}/following`);
        setFollowing(res.users || []);
      })();
    }
  }, [showFollowingModal, profileUser]);

  if (!profileUser) {
    return <p className="text-white">Loading profile...</p>;
  }

  const filteredAlbums = albums.filter((a) => {
    if (activeTab === "want") return a.status === "want-to-listen";
    if (activeTab === "listened") return a.status === "listened";
    if (activeTab === "favorites") return a.is_favorite;
    return false;
  });

  // Upload profile picture when avatar clicked
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/users/${profileUser.id}/profile-picture`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
        },
        body: formData,
      }
    );

    const updated = await apiFetch(`/users/by-username/${profileUser.username}`);
    setProfileUser(updated);
  };

  const toggleFollow = async () => {
    const action = profileUser.is_following ? "unfollow" : "follow";
    await apiFetch(`/users/${profileUser.id}/${action}`, {
      method: profileUser.is_following ? "DELETE" : "POST",
    });

    setProfileUser({
      ...profileUser,
      is_following: !profileUser.is_following,
      followers_count: profileUser.is_following
        ? profileUser.followers_count - 1
        : profileUser.followers_count + 1,
    });
  };

  return (
    <div className="max-w-4xl mx-auto mt-8 text-white">
      {/* Avatar (clickable to upload if own profile) */}
      <div className="relative inline-block">
        {isOwnProfile ? (
          <label htmlFor="profilePicInput" className="cursor-pointer">
            <UserAvatar
              username={profileUser.username}
              profilePicture={profileUser.profile_picture}
              size={140}
              editable={true}
            />
          </label>
        ) : (
          <UserAvatar
            username={profileUser.username}
            profilePicture={profileUser.profile_picture}
            size={140}
            onClick={() => setShowAvatarModal(true)} // 👈 open enlarge modal
          />
        )}

        {isOwnProfile && (
          <input
            id="profilePicInput"
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
        )}
      </div>

      {/* Avatar Enlarge Modal */}
      <Modal
        isOpen={showAvatarModal}
        onClose={() => setShowAvatarModal(false)}
        noScroll
        bare
      >
        <div className="flex justify-center items-center">
          <UserAvatar
            username={profileUser.username}
            profilePicture={profileUser.profile_picture}
            size={300}
          />
        </div>
      </Modal>

      <h1 className="text-3xl font-bold mt-3">
        {isOwnProfile ? `${profileUser.username}` : `${profileUser.username}’s Music Shelf`}
      </h1>

      {/* Followers / Following counts */}
      <div className="mb-4 flex gap-6">
        <button onClick={() => setShowFollowersModal(true)} className="hover:underline">
          <strong>{profileUser.followers_count}</strong> Followers
        </button>
        <button onClick={() => setShowFollowingModal(true)} className="hover:underline">
          <strong>{profileUser.following_count}</strong> Following
        </button>
      </div>

      {/* Mutual followers with avatars */}
      {!isOwnProfile && profileUser.mutual_followers?.length > 0 && (
        <div className="flex items-center gap-2 mt-2">
          {profileUser.mutual_followers.map((u: any) => (
            <Link
              key={u.id}
              href={`/profile/${u.username}`}
              className="flex items-center gap-2"
            >
              <UserAvatar username={u.username} profilePicture={u.profile_picture} size={20} />
              <span className="text-sm hover:underline">{u.username}</span>
            </Link>
          ))}
          {profileUser.mutual_followers_count > profileUser.mutual_followers.length && (
            <span className="text-sm text-gray-400">
              + {profileUser.mutual_followers_count - profileUser.mutual_followers.length} more
            </span>
          )}
        </div>
      )}

      {/* Follow/Unfollow button */}
      {!isOwnProfile && (
        <button
          onClick={toggleFollow}
          className={`mt-2 px-4 py-2 rounded font-medium ${
            profileUser.is_following ? "bg-gray-700 text-white" : "bg-indigo-500 text-white"
          }`}
        >
          {profileUser.is_following ? "Unfollow" : "Follow"}
        </button>
      )}

      {/* Followers Modal */}
      <Modal
        isOpen={showFollowersModal}
        onClose={() => setShowFollowersModal(false)}
        title="Followers"
      >
        {followers.length > 0 ? (
          followers.map((u: any) => (
            <div key={u.id} className="flex items-center gap-3">
              <Link
                href={`/profile/${u.username}`}
                className="flex items-center font-medium hover:underline gap-3"
                onClick={() => setShowFollowersModal(false)}
              >
                <UserAvatar username={u.username} profilePicture={u.profile_picture} size={32} />
                {u.username}
              </Link>
            </div>
          ))
        ) : (
          <p className="text-gray-400">No followers yet.</p>
        )}
      </Modal>

      {/* Following Modal */}
      <Modal
        isOpen={showFollowingModal}
        onClose={() => setShowFollowingModal(false)}
        title="Following"
      >
        {following.length > 0 ? (
          following.map((u: any) => (
            <div key={u.id} className="flex items-center gap-3">
              <Link
                href={`/profile/${u.username}`}
                className="flex items-center gap-3 font-medium hover:underline"
                onClick={() => setShowFollowingModal(false)}
              >
                <UserAvatar username={u.username} profilePicture={u.profile_picture} size={32} />
                {u.username}
              </Link>
            </div>
          ))
        ) : (
          <p className="text-gray-400">Not following anyone yet.</p>
        )}
      </Modal>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-700 my-6">
        {["want", "listened", "favorites", "reviews"].map((tab) => (
          <button
            key={tab}
            className={`pb-2 ${
              activeTab === tab
                ? "border-b-2 border-indigo-500 text-indigo-400"
                : "text-gray-400"
            }`}
            onClick={() =>
              setActiveTab(tab as "want" | "listened" | "favorites" | "reviews")
            }
          >
            {tab === "want"
              ? "Want to Listen"
              : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === "reviews" ? (
        <div className="space-y-4">
          {reviews.length > 0 ? (
            reviews.map((r) => (
              <ReviewCard
                key={r.id}
                username={r.user.username}
                profilePicture={r.user.profile_picture}
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