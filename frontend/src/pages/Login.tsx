import { useState, useEffect } from 'react'
import { Twitch, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { api } from '../api'
import { User, SystemCheck } from '../types'

interface LoginProps {
  onLogin: (user: User) => void
}

export default function Login({ onLogin }: LoginProps) {
  const [systemCheck, setSystemCheck] = useState<SystemCheck | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkSystem()
    
    // Check for callback params
    const params = new URLSearchParams(window.location.search)
    const userData = params.get('user')
    if (userData) {
      try {
        const user = JSON.parse(decodeURIComponent(userData))
        onLogin(user)
        window.history.replaceState({}, '', '/')
      } catch (e) {
        console.error('Invalid user data')
      }
    }
  }, [])

  const checkSystem = async () => {
    try {
      const check = await api.checkSystem()
      setSystemCheck(check)
    } catch (err) {
      setError('Impossible de se connecter au serveur. Assurez-vous que le backend est lancé.')
    } finally {
      setLoading(false)
    }
  }

  const handleTwitchLogin = () => {
    window.location.href = api.getTwitchLoginUrl()
  }

  const allDependenciesOk = systemCheck && 
    systemCheck.checks.ffmpeg.installed &&
    systemCheck.checks.yt_dlp.installed &&
    systemCheck.checks.ollama[0] &&
    systemCheck.checks.twitch_api.configured

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <img src="/nexus.svg" alt="Nexus" className="w-20 h-20 mx-auto mb-4" />
          <h1 className="text-3xl font-bold bg-gradient-to-r from-twitch-purple to-pink-500 bg-clip-text text-transparent">
            Nexus
          </h1>
          <p className="text-gray-400 mt-2">
            Transforme tes VODs Twitch en clips viraux
          </p>
        </div>

        <div className="card p-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-twitch-purple" />
            </div>
          ) : error ? (
            <div className="text-center py-4">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
              <p className="text-red-400">{error}</p>
              <button 
                onClick={checkSystem}
                className="btn-secondary mt-4"
              >
                Réessayer
              </button>
            </div>
          ) : (
            <>
              {/* System status */}
              <div className="mb-6 space-y-3">
                <h3 className="font-medium text-sm text-gray-400 uppercase tracking-wide">
                  État du système
                </h3>
                
                <StatusItem 
                  label="FFmpeg" 
                  ok={systemCheck?.checks.ffmpeg.installed || false}
                />
                <StatusItem 
                  label="yt-dlp" 
                  ok={systemCheck?.checks.yt_dlp.installed || false}
                />
                <StatusItem 
                  label="Ollama (LLM)" 
                  ok={systemCheck?.checks.ollama[0] || false}
                  detail={systemCheck?.checks.ollama[1]}
                />
                <StatusItem 
                  label="Twitch API" 
                  ok={systemCheck?.checks.twitch_api.configured || false}
                />
              </div>

              {/* Login button */}
              <button
                onClick={handleTwitchLogin}
                disabled={!allDependenciesOk}
                className="w-full py-3 bg-twitch-purple hover:bg-purple-600 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium flex items-center justify-center gap-3 transition-colors"
              >
                <Twitch size={20} />
                Connexion avec Twitch
              </button>

              {!allDependenciesOk && (
                <p className="text-sm text-gray-400 text-center mt-4">
                  Installez les dépendances manquantes avant de continuer.
                  <br />
                  Voir le fichier <code className="text-twitch-purple">TODO.md</code>
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function StatusItem({ label, ok, detail }: { label: string; ok: boolean; detail?: string }) {
  return (
    <div className="flex items-center justify-between py-2 px-3 bg-twitch-dark rounded-lg">
      <span className="text-sm">{label}</span>
      <div className="flex items-center gap-2">
        {detail && !ok && (
          <span className="text-xs text-gray-500 max-w-32 truncate">{detail}</span>
        )}
        {ok ? (
          <CheckCircle size={18} className="text-green-500" />
        ) : (
          <AlertCircle size={18} className="text-red-500" />
        )}
      </div>
    </div>
  )
}
