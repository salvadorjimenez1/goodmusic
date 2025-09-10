import Image from "next/image"
import Link from "next/link"

interface AlbumCardProps {
  id: string
  title: string
  artist: string
  coverUrl: string
}

export default function AlbumCard({ id, title, artist, coverUrl }: AlbumCardProps) {
  return (
    <Link href={`/album/${id}`}>
      <div className="bg-white rounded-2xl shadow-md overflow-hidden hover:shadow-lg transition cursor-pointer">
        <Image
          src={coverUrl}
          alt={`${title} cover`}
          width={300}
          height={300}
          className="w-full h-48 object-cover"
        />
        <div className="p-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-gray-600">{artist}</p>
        </div>
      </div>
    </Link>
  )
}