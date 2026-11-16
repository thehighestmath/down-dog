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
      durationMin:
        typeof durationMin === 'number' &&
        (DURATIONS as readonly number[]).includes(durationMin)
          ? durationMin
          : DEFAULT_SETTINGS.durationMin,
      level:
        typeof level === 'string' && LEVEL_OPTIONS.some((o) => o.value === level)
          ? level
          : DEFAULT_SETTINGS.level,
      focus:
        typeof focus === 'string' && FOCUS_OPTIONS.some((o) => o.value === focus)
          ? focus
          : DEFAULT_SETTINGS.focus,
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
