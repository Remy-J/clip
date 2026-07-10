import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Download, Search, Filter } from 'lucide-react'
import { User, VOD, ProcessingStatus } from '../types'
import { api } from '../api'
import VODCard from '../components/VODCard'

interface VODsProps {
  user: User
}

export default function VODs({ user }: VODsProps) {
  const [vods, setVods] = useState<VOD[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all')
  const [processingVods, setProcessingVods] = useState<Map<number, ProcessingStatus>>(new Map())

  useEffect(() => {
    loadVODs()
  }, [user.id])

  // Poll processing status
  useEffect(() => {
    const processingIds = Array.from(processingVods.entries())
      .filter(([_, status]) => status.status === 'processing')
      .map(([id]) => id)

    if (processingIds.length === 0) return

    const interval = setInterval(async () => {
      for (const vodId of processingIds) {
        const status = await api.getProcessingStatus(vodId)
        setProcessingVods(prev => {
          const next = new Map(prev)
          if (status.status === 'idle') {
            next.delete(vodId)
            loadVODs() // Refresh to get updated status
          } else {
            next.set(vodId, status)
          }
          return next
        })
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [processingVods])

  const loadVODs = async () => {
    setLoading(true)
    try {
      const data = await api.getLocalVODs(user.id)
      setVods(data.vods)
    } catch (error) {
      console.error('Error loading VODs:', error)
    } finally {
      setLoading(false)
    }
  }

  const syncFromTwitch = async () => {
    setSyncing(true)
    try {
      const data = await api.getVODs(user.id)
      setVods(data.vods)
    } catch (error) {
      console.error('Error syncing VODs:', error)
    } finally {
      setSyncing(false)
    }
  }

  const handleProcess = async (vod: VOD) => {
    try {
      await api.processVOD(vod.id)
      setProcessingVods(prev => {
        const next = new Map(prev)
        next.set(vod.id, { status: 'processing', progress: 0, message: 'Démarrage...' })
        return next
      })
    } catch (error) {
      console.error('Error processing VOD:', error)
    }
  }

  const filteredVods = vods.filter(vod => {
    const matchesSearch = vod.title.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === 'all' || 
      (filter === 'pending' && vod.status === 'pending') ||
      (filter === 'completed' && vod.status === 'completed')
    return matchesSearch && matchesFilter
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Mes VODs</h1>
          <p className="text-gray-400">{vods.length} VODs disponibles</p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={loadVODs}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Actualiser</span>
          </button>
          <button
            onClick={syncFromTwitch}
            disabled={syncing}
            className="btn-primary flex items-center gap-2"
          >
            <Download size={18} className={syncing ? 'animate-bounce' : ''} />
            Sync Twitch
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher une VOD..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
        
        <div className="flex gap-2">
          {(['all', 'pending', 'completed'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === f 
                  ? 'bg-twitch-purple text-white' 
                  : 'bg-twitch-gray text-gray-400 hover:text-white'
              }`}
            >
              {f === 'all' ? 'Toutes' : f === 'pending' ? 'En attente' : 'Terminées'}
            </button>
          ))}
        </div>
      </div>

      {/* VOD Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="aspect-video bg-gray-700" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-700 rounded w-3/4" />
                <div className="h-3 bg-gray-700 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredVods.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVods.map(vod => {
            const processingStatus = processingVods.get(vod.id)
            return (
              <VODCard
                key={vod.id}
                vod={vod}
                onProcess={handleProcess}
                processing={processingStatus?.status === 'processing'}
                progress={processingStatus?.progress}
                progressMessage={processingStatus?.message}
              />
            )
          })}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <p className="text-gray-400 mb-4">
            {search || filter !== 'all' 
              ? 'Aucune VOD ne correspond à ta recherche'
              : 'Aucune VOD trouvée'
            }
          </p>
          {!search && filter === 'all' && (
            <button onClick={syncFromTwitch} className="btn-primary">
              Importer depuis Twitch
            </button>
          )}
        </div>
      )}
    </div>
  )
}
