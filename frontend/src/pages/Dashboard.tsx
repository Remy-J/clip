import { useState, useEffect } from 'react'
import { Video, Scissors, Youtube, Instagram, TrendingUp, RefreshCw } from 'lucide-react'
import { User, VOD, Clip } from '../types'
import { api } from '../api'
import StatCard from '../components/StatCard'
import VODCard from '../components/VODCard'
import ClipCard from '../components/ClipCard'

interface DashboardProps {
  user: User
}

export default function Dashboard({ user }: DashboardProps) {
  const [vods, setVods] = useState<VOD[]>([])
  const [clips, setClips] = useState<Clip[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [user.id])

  const loadData = async () => {
    setLoading(true)
    try {
      const [vodsData, clipsData] = await Promise.all([
        api.getLocalVODs(user.id),
        api.getClips(user.id),
      ])
      setVods(vodsData.vods)
      setClips(clipsData.clips)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    totalVods: vods.length,
    totalClips: clips.length,
    publishedYoutube: clips.filter(c => c.youtube_url).length,
    publishedInstagram: clips.filter(c => c.instagram_url).length,
  }

  const recentVods = vods.slice(0, 3)
  const recentClips = clips.slice(0, 4)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Bonjour, {user.display_name} !</h1>
          <p className="text-gray-400">Voici un aperçu de ton activité</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          icon={Video} 
          label="VODs importées" 
          value={stats.totalVods}
          color="text-blue-500"
        />
        <StatCard 
          icon={Scissors} 
          label="Clips créés" 
          value={stats.totalClips}
          color="text-twitch-purple"
        />
        <StatCard 
          icon={Youtube} 
          label="Shorts publiés" 
          value={stats.publishedYoutube}
          color="text-red-500"
        />
        <StatCard 
          icon={Instagram} 
          label="Reels publiés" 
          value={stats.publishedInstagram}
          color="text-pink-500"
        />
      </div>

      {/* Recent VODs */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">VODs récentes</h2>
          <a href="/vods" className="text-twitch-purple hover:underline text-sm">
            Voir tout →
          </a>
        </div>
        
        {recentVods.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentVods.map(vod => (
              <VODCard 
                key={vod.id} 
                vod={vod} 
                onProcess={() => {}}
              />
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center">
            <Video className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">Aucune VOD importée</p>
            <a href="/vods" className="btn-primary inline-block mt-4">
              Importer des VODs
            </a>
          </div>
        )}
      </section>

      {/* Recent Clips */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Clips récents</h2>
          <a href="/clips" className="text-twitch-purple hover:underline text-sm">
            Voir tout →
          </a>
        </div>
        
        {recentClips.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {recentClips.map(clip => (
              <ClipCard 
                key={clip.id} 
                clip={clip}
                onPublished={loadData}
              />
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center">
            <Scissors className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">Aucun clip créé</p>
            <p className="text-sm text-gray-500 mt-2">
              Traite une VOD pour générer des clips automatiquement
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
