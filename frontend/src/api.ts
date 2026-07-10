import axios from 'axios'
import { VOD, Clip, ProcessingStatus, SystemCheck, User } from './types'

const client = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // System
  async checkSystem(): Promise<SystemCheck> {
    const { data } = await client.get('/api/system/check')
    return data
  },

  async getSetupGuide() {
    const { data } = await client.get('/api/system/setup-guide')
    return data
  },

  // Auth
  getTwitchLoginUrl(): string {
    return '/auth/twitch/login'
  },

  async getAuthStatus() {
    const { data } = await client.get('/auth/twitch/status')
    return data
  },

  // VODs
  async getVODs(userId: number): Promise<{ vods: VOD[] }> {
    const { data } = await client.get(`/api/twitch/vods?user_id=${userId}`)
    return data
  },

  async getLocalVODs(userId: number): Promise<{ vods: VOD[] }> {
    const { data } = await client.get(`/api/twitch/vods/local?user_id=${userId}`)
    return data
  },

  // Processing
  async processVOD(vodId: number, options: {
    max_clips?: number
    add_subtitles?: boolean
    subtitle_style?: string
  } = {}): Promise<{ message: string; vod_id: number }> {
    const { data } = await client.post('/api/clips/process', {
      vod_id: vodId,
      max_clips: options.max_clips ?? 5,
      add_subtitles: options.add_subtitles ?? true,
      subtitle_style: options.subtitle_style ?? 'modern',
    })
    return data
  },

  async getProcessingStatus(vodId: number): Promise<ProcessingStatus> {
    const { data } = await client.get(`/api/clips/process/${vodId}/status`)
    return data
  },

  // Clips
  async getClips(userId: number): Promise<{ clips: Clip[] }> {
    const { data } = await client.get(`/api/clips/user/${userId}`)
    return data
  },

  async publishClip(clipId: number, platforms: string[], options: {
    youtube_title?: string
    youtube_description?: string
    instagram_caption?: string
  } = {}): Promise<{ results: Record<string, unknown> }> {
    const { data } = await client.post('/api/clips/publish', {
      clip_id: clipId,
      platforms,
      ...options,
    })
    return data
  },
}
