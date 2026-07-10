export interface User {
  id: number
  twitch_id: string
  login: string
  display_name: string
  profile_image: string | null
}

export interface VOD {
  id: number
  twitch_vod_id: string
  title: string
  duration_seconds: number
  duration_formatted: string
  view_count: number
  thumbnail_url: string | null
  twitch_url: string
  status: 'pending' | 'downloading' | 'processing' | 'completed' | 'error'
  download_progress: number
  analysis_progress: number
  created_at: string
}

export interface Clip {
  id: number
  title: string
  description: string | null
  duration: number
  local_path: string
  thumbnail_path: string | null
  has_subtitles: boolean
  youtube_url: string | null
  instagram_url: string | null
  status: string
  created_at: string
}

export interface ProcessingStatus {
  status: 'idle' | 'processing' | 'error'
  stage?: string
  progress?: number
  message?: string
}

export interface SystemCheck {
  status: 'ok' | 'missing_dependencies'
  checks: {
    ffmpeg: { installed: boolean }
    yt_dlp: { installed: boolean }
    ollama: [boolean, string]
    twitch_api: { configured: boolean }
  }
}
