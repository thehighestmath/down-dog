export interface Pose {
  id: number
  name_ru: string
  name_sanskrit: string | null
  name_en: string
  category: string
  difficulty: string
  focus_areas: string
  contraindications: string | null
  description: string | null
  image_url: string | null
  audio_url: string | null
  hold_time_sec: number | null
  full_cycle_sec: number | null
}

export interface Workout {
  id: string
  duration_min: number
  level: string
  focus: string
  poses: string[]
}

export type View = 'home' | 'player' | 'finished'

export interface PlaylistItem {
  name: string
  pose: Pose | undefined
  duration: number
}