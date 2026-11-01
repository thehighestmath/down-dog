import { API_URL } from './constants'
import type { PlaylistItem } from './types'

export const AudioLang = {
  Ru: 'ru',
  En: 'en',
} as const
export type AudioLang = (typeof AudioLang)[keyof typeof AudioLang]

export const AudioKind = {
  Poses: 'poses',
  Phrases: 'phrases',
  Numbers: 'numbers',
} as const
export type AudioKind = (typeof AudioKind)[keyof typeof AudioKind]

export const Phrase = {
  Start: 'start',
  Enter: 'enter',
  Breathe: 'breathe',
  Hold: 'hold',
  Seconds: 'seconds',
  Next: 'next',
  Finish: 'finish',
} as const
export type Phrase = (typeof Phrase)[keyof typeof Phrase]

function url(lang: AudioLang, kind: AudioKind, name: string): string {
  return `${API_URL}/audio/${lang}/${kind}/${encodeURIComponent(name)}`
}

export function phraseUrl(lang: AudioLang, phrase: Phrase): string {
  return url(lang, AudioKind.Phrases, phrase)
}

export function poseIntroUrls(
  item: PlaylistItem,
  isFirst: boolean,
  lang: AudioLang,
): string[] {
  const urls = isFirst
    ? [phraseUrl(lang, Phrase.Start)]
    : [phraseUrl(lang, Phrase.Next), phraseUrl(lang, Phrase.Enter)]
  if (item.pose?.audio_name) {
    urls.push(url(lang, AudioKind.Poses, item.pose.audio_name))
  }
  urls.push(
    phraseUrl(lang, Phrase.Hold),
    url(lang, AudioKind.Numbers, String(item.duration)),
    phraseUrl(lang, Phrase.Seconds),
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
