import { useState, useEffect } from 'react'
import { 
  Settings as SettingsIcon, 
  CheckCircle, 
  AlertCircle, 
  ExternalLink,
  RefreshCw,
  Youtube,
  Instagram,
  Cpu,
  HardDrive,
  Subtitles
} from 'lucide-react'
import { api } from '../api'
import { SystemCheck } from '../types'

export default function Settings() {
  const [systemCheck, setSystemCheck] = useState<SystemCheck | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Settings state (would be persisted to backend in a real app)
  const [settings, setSettings] = useState({
    max_clips: 5,
    add_subtitles: true,
    subtitle_style: 'modern',
    whisper_model: 'small',
    ollama_model: 'llama3.1:8b',
  })

  useEffect(() => {
    loadSystemCheck()
  }, [])

  const loadSystemCheck = async () => {
    setLoading(true)
    try {
      const check = await api.checkSystem()
      setSystemCheck(check)
    } catch (error) {
      console.error('Error checking system:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Paramètres</h1>
        <p className="text-gray-400">Configure Nexus selon tes préférences</p>
      </div>

      {/* System Status */}
      <section className="card">
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Cpu className="text-twitch-purple" />
            <h2 className="font-semibold">État du système</h2>
          </div>
          <button
            onClick={loadSystemCheck}
            disabled={loading}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Vérifier
          </button>
        </div>
        
        <div className="p-4 space-y-3">
          <StatusRow 
            label="FFmpeg"
            description="Traitement vidéo"
            ok={systemCheck?.checks.ffmpeg.installed || false}
            loading={loading}
          />
          <StatusRow 
            label="yt-dlp"
            description="Téléchargement VODs"
            ok={systemCheck?.checks.yt_dlp.installed || false}
            loading={loading}
          />
          <StatusRow 
            label="Ollama"
            description="LLM local pour l'analyse"
            ok={systemCheck?.checks.ollama[0] || false}
            detail={systemCheck?.checks.ollama[1]}
            loading={loading}
          />
          <StatusRow 
            label="Twitch API"
            description="Connexion à Twitch"
            ok={systemCheck?.checks.twitch_api.configured || false}
            loading={loading}
          />
        </div>
      </section>

      {/* Clip Generation Settings */}
      <section className="card">
        <div className="p-4 border-b border-gray-700 flex items-center gap-3">
          <Subtitles className="text-twitch-purple" />
          <h2 className="font-semibold">Génération de clips</h2>
        </div>
        
        <div className="p-4 space-y-6">
          {/* Max clips */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Nombre maximum de clips par VOD
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={settings.max_clips}
              onChange={(e) => setSettings({ ...settings, max_clips: parseInt(e.target.value) })}
              className="w-full accent-twitch-purple"
            />
            <div className="flex justify-between text-sm text-gray-400 mt-1">
              <span>1</span>
              <span className="text-twitch-purple font-medium">{settings.max_clips}</span>
              <span>20</span>
            </div>
          </div>

          {/* Subtitles */}
          <div>
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="font-medium">Sous-titres automatiques</p>
                <p className="text-sm text-gray-400">Ajoute des sous-titres aux clips</p>
              </div>
              <div className={`w-12 h-6 rounded-full p-1 transition-colors ${
                settings.add_subtitles ? 'bg-twitch-purple' : 'bg-gray-600'
              }`}>
                <div className={`w-4 h-4 rounded-full bg-white transition-transform ${
                  settings.add_subtitles ? 'translate-x-6' : ''
                }`} />
              </div>
            </label>
          </div>

          {/* Subtitle style */}
          {settings.add_subtitles && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Style des sous-titres
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['modern', 'classic', 'bold'] as const).map(style => (
                  <button
                    key={style}
                    onClick={() => setSettings({ ...settings, subtitle_style: style })}
                    className={`p-3 rounded-lg border transition-colors ${
                      settings.subtitle_style === style
                        ? 'border-twitch-purple bg-twitch-purple/20'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <p className="font-medium capitalize">{style}</p>
                    <p className="text-xs text-gray-400">
                      {style === 'modern' && 'Blanc, contour noir'}
                      {style === 'classic' && 'Jaune, contour noir'}
                      {style === 'bold' && 'Grand, centré'}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* AI Models */}
      <section className="card">
        <div className="p-4 border-b border-gray-700 flex items-center gap-3">
          <HardDrive className="text-twitch-purple" />
          <h2 className="font-semibold">Modèles IA</h2>
        </div>
        
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Modèle Whisper (transcription)
            </label>
            <select
              value={settings.whisper_model}
              onChange={(e) => setSettings({ ...settings, whisper_model: e.target.value })}
              className="input"
            >
              <option value="tiny">tiny - Très rapide, moins précis</option>
              <option value="base">base - Rapide</option>
              <option value="small">small - Recommandé</option>
              <option value="medium">medium - Plus précis, plus lent</option>
              <option value="large-v3">large-v3 - Meilleure qualité (GPU recommandé)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Modèle LLM (analyse)
            </label>
            <select
              value={settings.ollama_model}
              onChange={(e) => setSettings({ ...settings, ollama_model: e.target.value })}
              className="input"
            >
              <option value="llama3.1:8b">Llama 3.1 8B - Recommandé</option>
              <option value="mistral:7b">Mistral 7B - Alternative légère</option>
              <option value="phi3:mini">Phi-3 Mini - Très léger</option>
            </select>
          </div>
        </div>
      </section>

      {/* Connected Services */}
      <section className="card">
        <div className="p-4 border-b border-gray-700 flex items-center gap-3">
          <SettingsIcon className="text-twitch-purple" />
          <h2 className="font-semibold">Services connectés</h2>
        </div>
        
        <div className="p-4 space-y-4">
          <ServiceRow 
            icon={Youtube}
            name="YouTube"
            description="Publie automatiquement tes Shorts"
            connected={false}
            color="text-red-500"
          />
          <ServiceRow 
            icon={Instagram}
            name="Instagram"
            description="Publie automatiquement tes Reels"
            connected={false}
            color="text-pink-500"
          />
        </div>
      </section>
    </div>
  )
}

interface StatusRowProps {
  label: string
  description: string
  ok: boolean
  detail?: string
  loading?: boolean
}

function StatusRow({ label, description, ok, detail, loading }: StatusRowProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-gray-400">{description}</p>
      </div>
      {loading ? (
        <div className="w-5 h-5 border-2 border-gray-600 border-t-twitch-purple rounded-full animate-spin" />
      ) : ok ? (
        <CheckCircle className="text-green-500" size={20} />
      ) : (
        <div className="flex items-center gap-2">
          {detail && <span className="text-xs text-gray-500">{detail}</span>}
          <AlertCircle className="text-red-500" size={20} />
        </div>
      )}
    </div>
  )
}

interface ServiceRowProps {
  icon: React.ComponentType<{ size: number; className?: string }>
  name: string
  description: string
  connected: boolean
  color: string
}

function ServiceRow({ icon: Icon, name, description, connected, color }: ServiceRowProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3">
        <Icon size={24} className={color} />
        <div>
          <p className="font-medium">{name}</p>
          <p className="text-sm text-gray-400">{description}</p>
        </div>
      </div>
      <button className={`btn text-sm ${connected ? 'btn-secondary' : 'btn-primary'}`}>
        {connected ? 'Connecté' : 'Connecter'}
      </button>
    </div>
  )
}
