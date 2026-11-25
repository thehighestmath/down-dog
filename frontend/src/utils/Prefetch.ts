import { poseIntroUrls, type AudioLang } from '../audio'
import type { PlaylistItem } from '../types'

// Через сколько после смены позы начинать предзагрузку. За это время уходит запрос
// за озвучкой текущей позы (он не должен конкурировать с предзагрузкой), а при серии
// нажатий «Пропустить» грузится только поза, на которой пользователь остановился.
export const PREFETCH_DELAY_MS = 500

// Ссылки на элементы, пока идёт загрузка: браузер может отменить загрузку
// элемента, на который никто не ссылается. Храним несколько последних.
const MAX_KEPT = 16
const kept: (HTMLImageElement | HTMLAudioElement)[] = []

function keep(el: HTMLImageElement | HTMLAudioElement): void {
  kept.push(el)
  if (kept.length > MAX_KEPT) kept.shift()
}

// Единственный источник URL картинки позы: его же берёт <img> в Player,
// чтобы ключ кэша у предзагрузки и у показа совпадал.
export function poseImageUrl(item: PlaylistItem): string | null {
  return item.pose?.image_url || null
}

// Загружает картинку и озвучку позы в кэш браузера, ничего не показывая и не играя.
export function prefetchPose(item: PlaylistItem, lang: AudioLang): void {
  const imageUrl = poseImageUrl(item)
  if (imageUrl) {
    const img = new Image()
    img.src = imageUrl
    keep(img)
    // Декодируем заранее, чтобы картинка появилась без мигания
    img.decode?.().catch(() => {})
  }

  // isFirst = false: предзагружаем всегда не первую позу тренировки.
  // Тот же <audio>-механизм, что и в AudioQueue, поэтому запрос уходит
  // с теми же заголовками (в том числе Range) и попадает в тот же кэш.
  for (const url of poseIntroUrls(item, false, lang)) {
    const audio = new Audio()
    audio.preload = 'auto' // загрузить, но не играть
    audio.src = url
    audio.load()
    keep(audio)
  }
}
