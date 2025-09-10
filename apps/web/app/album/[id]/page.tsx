import Image from "next/image"
import ReviewSection from "../../../components/ReviewSelection"
import AlbumActionButtons from "../../../components/AlbumActionButtons"


const albumData: Record<
  string,
  { title: string; artist: string; coverUrl: string; tracks: string[] }
> = {
  blonde: {
    title: "Blonde",
    artist: "Frank Ocean",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/a/a0/Blonde_-_Frank_Ocean.jpeg",
    tracks: ["Nikes", "Ivy", "Pink + White", "Self Control", "Nights"],
  },
  damn: {
    title: "DAMN.",
    artist: "Kendrick Lamar",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/5/51/Kendrick_Lamar_-_Damn.png",
    tracks: ["DNA.", "YAH.", "ELEMENT.", "LOYALTY.", "HUMBLE."],
  },
  tpab: {
    title: "To Pimp a Butterfly",
    artist: "Kendrick Lamar",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/f/f6/Kendrick_Lamar_-_To_Pimp_a_Butterfly.png",
    tracks: ["Wesley's Theory", "King Kunta", "Alright", "These Walls", "The Blacker the Berry"],
  },
  currents: {
    title: "Currents",
    artist: "Tame Impala",
    coverUrl: "https://upload.wikimedia.org/wikipedia/en/9/9b/Tame_Impala_-_Currents.png",
    tracks: ["Let It Happen", "The Moment", "Yes I'm Changing", "Eventually", "The Less I Know the Better"],
  },
}

interface Props {
  params: { id: string }
}

export default async function AlbumDetailPage({ params }: Props) {
  const album = albumData[params.id]

  if (!album) return <p className="text-red-500">Album not found</p>

  return (
    <div>
      {/* Album Info */}
      <div className="flex flex-col md:flex-row gap-6 mb-8 text-white">
        <Image
          src={album.coverUrl}
          alt={`${album.title} cover`}
          width={300}
          height={300}
          className="rounded-lg shadow-md"
        />
        <div>
          <h2 className="text-3xl font-bold">{album.title}</h2>
          <p className="text-lg text-gray-300">{album.artist}</p>
        </div>
      </div>

      {/* Album Action Buttons */}
      <AlbumActionButtons 
      albumId={params.id}
      title={album.title}
      artist={album.artist} />

      {/* Tracklist */}
      <h3 className="text-xl font-semibold mb- text-white">Tracklist</h3>
      <ul className="list-disc pl-6 space-y-1 mb-6">
         <ol  style={{ listStyleType: 'decimal'}} className="numbered-list text-white">
        {album.tracks.map((track, i) => (
          <li key={i}>{track}</li>
        ))}
        </ol>
      </ul>

      {/* Reviews Section (Client Component) */}
      <ReviewSection albumId={params.id} />
    </div>
  )
}