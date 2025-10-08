import { useEffect, useState } from "react";

function FollowButton({ userId, isFollowing }: { userId: number; isFollowing: boolean }) {
  const [following, setFollowing] = useState(isFollowing);

  const toggleFollow = async () => {
    const url = `http://localhost:8000/users/${userId}/${following ? "unfollow" : "follow"}`;
    const method = following ? "DELETE" : "POST";

    await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    });

    setFollowing(!following);
  };

  return (
    <button
      onClick={toggleFollow}
      className={`px-4 py-2 rounded font-medium ${
        following ? "bg-gray-200 text-black" : "bg-blue-500 text-white"
      }`}
    >
      {following ? "Unfollow" : "Follow"}
    </button>
  );
}