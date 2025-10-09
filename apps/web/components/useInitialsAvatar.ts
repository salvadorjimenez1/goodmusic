import { useEffect, useState } from "react";

function stringToColor(str: string) {
  const colors = [
    "#0D8ABC", "#F39C12", "#27AE60",
    "#8E44AD", "#E74C3C", "#16A085", "#2C3E50"
  ];
  const hash = str.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
}

export function useInitialsAvatar(username: string, size: number = 64) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Background color based on username
    ctx.fillStyle = stringToColor(username);
    ctx.fillRect(0, 0, size, size);

    // Draw initials
    const initials = username[0]?.toUpperCase() ?? "?";
    ctx.fillStyle = "#fff";
    ctx.font = `${size * 0.5}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(initials, size / 2, size / 2);

    // Convert canvas to blob URL
    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob);
        setUrl(url);
      }
    });

    // Cleanup
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [username, size]);

  return url;
}