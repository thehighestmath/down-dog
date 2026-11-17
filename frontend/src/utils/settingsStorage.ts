import { DURATIONS, FOCUS_OPTIONS, LEVEL_OPTIONS } from '../constants'

export interface Settings {
  durationMin: number
  level: string
  focus: string
}

// Значения по умолчанию совпадают с прежними useState в App.tsx
export const DEFAULT_SETTINGS: Settings = {
  durationMin: 15,
  level: 'beginner',
  focus: 'full_body',
}

const LEVELS = LEVEL_OPTIONS.map((o) => o.value)
const FOCUSES = FOCUS_OPTIONS.map((o) => o.value)

// Возвращает value, если оно есть в списке допустимых, иначе fallback
function pickAllowed<T>(value: unknown, allowed: readonly T[], fallback: T): T {
  return allowed.find((item) => item === value) ?? fallback
}

// Один ключ на все три значения (в localStorage лежит JSON).
// С префиксом, чтобы не пересечься с analytics_user_id из PR #40.
const STORAGE_KEY = 'down-dog:settings'

// Каждое поле проверяется отдельно: одно устаревшее значение
// не сбрасывает остальные.
export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_SETTINGS

    const data: unknown = JSON.parse(raw)
    if (typeof data !== 'object' || data === null) return DEFAULT_SETTINGS
    const { durationMin, level, focus } = data as Record<string, unknown>

    return {
      durationMin: pickAllowed(durationMin, DURATIONS, DEFAULT_SETTINGS.durationMin),
      level: pickAllowed(level, LEVELS, DEFAULT_SETTINGS.level),
      focus: pickAllowed(focus, FOCUSES, DEFAULT_SETTINGS.focus),
    }
  } catch {
    // localStorage недоступен или в нём не JSON: работаем со значениями по умолчанию
    return DEFAULT_SETTINGS
  }
}

export function saveSettings(settings: Settings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    // приватный режим или переполненное хранилище: работаем без сохранения
  }
}
