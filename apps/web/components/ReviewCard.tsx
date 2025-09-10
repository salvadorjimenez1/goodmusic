interface Props {
  username: string
  rating: number // 1-5
  comment: string
}

export default function ReviewCard({ username, rating, comment }: Props) {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm mb-3">
      <div className="flex justify-between items-center mb-2">
        <span className="font-semibold">{username}</span>
        <span className="text-yellow-500">{'★'.repeat(rating)}</span>
      </div>
      <p className="text-gray-700">{comment}</p>
    </div>
  )
}