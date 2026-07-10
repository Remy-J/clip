import { Play, Clock, Eye, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { VOD } from '../types'

interface VODCardProps {
  vod: VOD
  onProcess: (vod: VOD) => void
  processing?: boolean
  progress?: number
  progressMessage?: string
}

export default function VODCard({ vod, onProcess, processing, progress, progressMessage }: VODCardProps) {
  const statusColors = {
    pending: 'bg-gray-600',
    downloading: 'bg-blue-600',
    processing: 'bg-yellow-600',
    completed: 'bg-green-600',
    error: 'bg-red-600',
  }

  const statusLabels = {
    pending: 'En attente',
    downloading: 'Téléchargement',
    processing: 'Traitement',
    completed: 'Terminé',
    error: 'Erreur',
  }

  const thumbnailUrl = vod.thumbnail_url || 'https://static-cdn.jtvnw.net/ttv-static/404_preview-320x180.jpg'

  return (
    <div className="card group">
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-800">
        <img 
          src={thumbnailUrl} 
          alt={vod.title}
          className="w-full h-full object-cover"
        />
        
        {/* Duration badge */}
        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 rounded text-sm font-medium">
          {vod.duration_formatted}
        </div>

        {/* Status badge */}
        {vod.status !== 'pending' && (
          <div className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-medium ${statusColors[vod.status]}`}>
            {statusLabels[vod.status]}
          </div>
        )}

        {/* Processing overlay */}
        {processing && (
          <div className="absolute inset-0 bg-black/70 flex flex-col items-center justify-center">
            <Loader2 className="w-10 h-10 animate-spin text-twitch-purple mb-2" />
            <p className="text-sm font-medium">{Math.round((progress || 0) * 100)}%</p>
            <p className="text-xs text-gray-400 mt-1">{progressMessage}</p>
          </div>
        )}

        {/* Hover overlay */}
        {!processing && vod.status === 'pending' && (
          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <button
              onClick={() => onProcess(vod)}
              className="btn-primary flex items-center gap-2"
            >
              <Play size={18} />
              Traiter
            </button>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        <h3 className="font-medium line-clamp-2 mb-2">{vod.title}</h3>
        
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <div className="flex items-center gap-1">
            <Eye size={14} />
            <span>{vod.view_count.toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock size={14} />
            <span>{new Date(vod.created_at).toLocaleDateString('fr-FR')}</span>
          </div>
        </div>

        {/* Progress bar for processing */}
        {processing && progress !== undefined && (
          <div className="mt-3">
            <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-twitch-purple transition-all duration-300"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Completed indicator */}
        {vod.status === 'completed' && (
          <div className="mt-3 flex items-center gap-2 text-green-500 text-sm">
            <CheckCircle size={16} />
            <span>Clips générés</span>
          </div>
        )}

        {/* Error indicator */}
        {vod.status === 'error' && (
          <div className="mt-3 flex items-center gap-2 text-red-500 text-sm">
            <AlertCircle size={16} />
            <span>Erreur de traitement</span>
          </div>
        )}
      </div>
    </div>
  )
}
