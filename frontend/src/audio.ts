import { API_URL } from './constants'
import type { PlaylistItem } from './types'

export type AudioLang = 'ru' | 'en'
export type PhraseKey =
  'start' | 'enter' | 'breathe' | 'hold' | 'seconds' | 'next' | 'finish'

function url(
  lang: AudioLang,
  kind: 'poses' | 'phrases' | 'numbers',
  name: string,
): string {
  return `${API_URL}/audio/${lang}/${kind}/${encodeURIComponent(name)}`
}

export function phraseUrl(lang: AudioLang, key: PhraseKey): string {
  return url(lang, 'phrases', key)
}

export function poseIntroUrls(
  item: PlaylistItem,
  isFirst: boolean,
  lang: AudioLang,
): string[] {
  const urls = isFirst
    ? [phraseUrl(lang, 'start')]
    : [phraseUrl(lang, 'next'), phraseUrl(lang, 'enter')]
  if (item.pose?.audio_name) {
    urls.push(url(lang, 'poses', item.pose.audio_name))
  }
  urls.push(
    phraseUrl(lang, 'hold'),
    url(lang, 'numbers', String(item.duration)),
    phraseUrl(lang, 'seconds'),
  )
  return urls
}

export class AudioQueue {
  private audio = new Audio()
  private queue: string[] = []
  private generation = 0

  constructor() {
    this.audio.onended = () => this.playNext(this.generation)
    this.audio.onerror = () => this.playNext(this.generation)
  }

  play(urls: string[]): void {
    this.generation += 1
    this.queue = [...urls]
    this.playNext(this.generation)
  }

  pause(): void {
    this.audio.pause()
  }

  resume(): void {
    if (this.audio.src && this.audio.paused && !this.audio.ended) {
      this.audio.play().catch(() => {})
    }
  }

  stop(): void {
    this.generation += 1
    this.queue = []
    this.audio.pause()
  }

  private playNext(gen: number): void {
    if (gen !== this.generation) return
    const next = this.queue.shift()
    if (!next) return
    this.audio.src = next
    this.audio.play().catch(() => this.playNext(gen))
  }
}
