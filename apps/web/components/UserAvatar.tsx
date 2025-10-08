import Image from "next/image";
import { Camera } from "lucide-react";

const colors = [
  "bg-red-500", "bg-blue-500", "bg-green-500", "bg-yellow-500",
  "bg-purple-500", "bg-pink-500", "bg-indigo-500",
];

function getColor(username: string) {
  const hash = username.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
}

export default function UserAvatar({
  username,
  profilePicture,
  size = 40,
  editable = false,
  onClick,
}: {
  username: string;
  profilePicture?: string | null;
  size?: number;
  editable?: boolean;
  onClick?: () => void;
}) {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const src = profilePicture
    ? profilePicture.startsWith("http")
      ? profilePicture
      : API_BASE + profilePicture
    : null;

  if (src) {
    return (
      <div
        onClick={onClick}
        className={`relative inline-block rounded-full group cursor-pointer`}
        style={{ width: size, height: size }}
      >
        <Image
          src={src}
          alt={username}
          width={size}
          height={size}
          className="rounded-full object-cover"
        />
        {editable && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
            <Camera className="text-white w-1/3 h-1/3" />
          </div>
        )}
      </div>
    );
  }

  // fallback initials
  const initials = username
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      onClick={onClick}
      className={`relative flex items-center justify-center rounded-full group cursor-pointer ${getColor(
        username
      )} text-white`}
      style={{ width: size, height: size, fontSize: size / 2 }}
    >
      {initials}
      {editable && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
          <Camera className="text-white w-1/3 h-1/3" />
        </div>
      )}
    </div>
  );
}