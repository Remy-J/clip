import { useState } from 'react'
import { 
  Play, 
  Youtube, 
  Instagram, 
  Share2, 
  Check,
  Loader2,
  Subtitles
} from 'lucide-react'
import { Clip } from '../types'
import { api } from '../api'

interface ClipCardProps {
  clip: Clip
  onPublished: () => void
}

export default function ClipCard({ clip, onPublished }: ClipCardProps) {
  const [publishing, setPublishing] = useState<string | null>(null)
  const [showShareMenu, setShowShareMenu] = useState(false)

  const handlePublish = async (platform: 'youtube' | 'instagram') => {
    setPublishing(platform)
    try {
      await api.publishClip(clip.id, [platform])
      onPublished()
    } catch (error) {
      console.error('Publish error:', error)
    } finally {
      setPublishing(null)
      setShowShareMenu(false)
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="card group">
      {/* Thumbnail */}
      <div className="relative aspect-[9/16] bg-gray-800 max-h-64">
        {clip.thumbnail_path ? (
          <img 
            src={`/data/clips/${clip.thumbnail_path.split('/').pop()}`}
            alt={clip.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Play size={48} className="text-gray-600" />
          </div>
        )}

        {/* Duration */}
        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 rounded text-sm">
          {formatDuration(clip.duration)}
        </div>

        {/* Subtitles badge */}
        {clip.has_subtitles && (
          <div className="absolute top-2 left-2 p-1.5 bg-black/80 rounded">
            <Subtitles size={14} />
          </div>
        )}

        {/* Published badges */}
        <div className="absolute top-2 right-2 flex gap-1">
          {clip.youtube_url && (
            <a 
              href={clip.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 bg-red-600 rounded hover:bg-red-700 transition-colors"
            >
              <Youtube size={14} />
            </a>
          )}
          {clip.instagram_url && (
            <a
              href={clip.instagram_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 bg-gradient-to-br from-purple-600 to-pink-500 rounded hover:opacity-90 transition-opacity"
            >
              <Instagram size={14} />
            </a>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <h3 className="font-medium line-clamp-2 mb-2">{clip.title}</h3>
        
        {clip.description && (
          <p className="text-sm text-gray-400 line-clamp-2 mb-3">{clip.description}</p>
        )}

        <div className="flex items-center gap-2">
          {/* Share button */}
          <div className="relative flex-1">
            <button
              onClick={() => setShowShareMenu(!showShareMenu)}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              <Share2 size={16} />
              Publier
            </button>

            {/* Share menu */}
            {showShareMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-twitch-gray border border-gray-600 rounded-lg overflow-hidden shadow-xl z-10">
                <button
                  onClick={() => handlePublish('youtube')}
                  disabled={!!clip.youtube_url || publishing === 'youtube'}
                  className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-700 transition-colors disabled:opacity-50"
                >
                  {publishing === 'youtube' ? (
                    <Loader2 size={18} className="animate-spin text-red-500" />
                  ) : clip.youtube_url ? (
                    <Check size={18} className="text-green-500" />
                  ) : (
                    <Youtube size={18} className="text-red-500" />
                  )}
                  <span>YouTube Shorts</span>
                </button>
                
                <button
                  onClick={() => handlePublish('instagram')}
                  disabled={!!clip.instagram_url || publishing === 'instagram'}
                  className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-700 transition-colors disabled:opacity-50"
                >
                  {publishing === 'instagram' ? (
                    <Loader2 size={18} className="animate-spin text-pink-500" />
                  ) : clip.instagram_url ? (
                    <Check size={18} className="text-green-500" />
                  ) : (
                    <Instagram size={18} className="text-pink-500" />
                  )}
                  <span>Instagram Reels</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
