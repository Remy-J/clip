import { useState, useEffect } from 'react'
import { RefreshCw, Search, Filter, Youtube, Instagram, Scissors } from 'lucide-react'
import { User, Clip } from '../types'
import { api } from '../api'
import ClipCard from '../components/ClipCard'

interface ClipsProps {
  user: User
}

export default function Clips({ user }: ClipsProps) {
  const [clips, setClips] = useState<Clip[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'youtube' | 'instagram' | 'unpublished'>('all')

  useEffect(() => {
    loadClips()
  }, [user.id])

  const loadClips = async () => {
    setLoading(true)
    try {
      const data = await api.getClips(user.id)
      setClips(data.clips)
    } catch (error) {
      console.error('Error loading clips:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredClips = clips.filter(clip => {
    const matchesSearch = clip.title.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === 'all' ||
      (filter === 'youtube' && clip.youtube_url) ||
      (filter === 'instagram' && clip.instagram_url) ||
      (filter === 'unpublished' && !clip.youtube_url && !clip.instagram_url)
    return matchesSearch && matchesFilter
  })

  const stats = {
    total: clips.length,
    youtube: clips.filter(c => c.youtube_url).length,
    instagram: clips.filter(c => c.instagram_url).length,
    unpublished: clips.filter(c => !c.youtube_url && !c.instagram_url).length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Mes Clips</h1>
          <p className="text-gray-400">
            {stats.total} clips • {stats.youtube} YouTube • {stats.instagram} Instagram
          </p>
        </div>
        
        <button
          onClick={loadClips}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un clip..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
        
        <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
          <FilterButton 
            active={filter === 'all'} 
            onClick={() => setFilter('all')}
            icon={Scissors}
            label="Tous"
            count={stats.total}
          />
          <FilterButton 
            active={filter === 'youtube'} 
            onClick={() => setFilter('youtube')}
            icon={Youtube}
            label="YouTube"
            count={stats.youtube}
            color="text-red-500"
          />
          <FilterButton 
            active={filter === 'instagram'} 
            onClick={() => setFilter('instagram')}
            icon={Instagram}
            label="Instagram"
            count={stats.instagram}
            color="text-pink-500"
          />
          <FilterButton 
            active={filter === 'unpublished'} 
            onClick={() => setFilter('unpublished')}
            label="Non publiés"
            count={stats.unpublished}
          />
        </div>
      </div>

      {/* Clips Grid */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="aspect-[9/16] max-h-64 bg-gray-700" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-700 rounded w-3/4" />
                <div className="h-3 bg-gray-700 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredClips.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filteredClips.map(clip => (
            <ClipCard 
              key={clip.id} 
              clip={clip}
              onPublished={loadClips}
            />
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <Scissors className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 mb-2">
            {search || filter !== 'all' 
              ? 'Aucun clip ne correspond à ta recherche'
              : 'Aucun clip créé'
            }
          </p>
          <p className="text-sm text-gray-500">
            Va dans l'onglet VODs et traite une vidéo pour générer des clips
          </p>
        </div>
      )}
    </div>
  )
}

interface FilterButtonProps {
  active: boolean
  onClick: () => void
  icon?: React.ComponentType<{ size: number; className?: string }>
  label: string
  count: number
  color?: string
}

function FilterButton({ active, onClick, icon: Icon, label, count, color }: FilterButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
        active 
          ? 'bg-twitch-purple text-white' 
          : 'bg-twitch-gray text-gray-400 hover:text-white'
      }`}
    >
      {Icon && <Icon size={16} className={active ? '' : color} />}
      <span>{label}</span>
      <span className={`px-1.5 py-0.5 rounded text-xs ${
        active ? 'bg-white/20' : 'bg-gray-700'
      }`}>
        {count}
      </span>
    </button>
  )
}
