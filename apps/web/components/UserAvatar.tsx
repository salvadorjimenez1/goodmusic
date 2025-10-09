import Image from "next/image";
import { Camera } from "lucide-react";
import { useInitialsAvatar } from "./useInitialsAvatar";

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
  const initialsUrl = useInitialsAvatar(username, size);

  const src = profilePicture
    ? profilePicture.startsWith("http")
      ? profilePicture
      : API_BASE + profilePicture
    : initialsUrl || ""; // fallback if still generating

  return (
    <div
      onClick={onClick}
      className="relative inline-block rounded-full group cursor-pointer"
      style={{ width: size, height: size }}
    >
      {src && (
        <Image
          src={src}
          alt={username}
          width={size}
          height={size}
          className="rounded-full object-cover"
        />
      )}
      {editable && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
          <Camera className="text-white w-1/3 h-1/3" />
        </div>
      )}
    </div>
  );
}