type AudioContextCtor = typeof AudioContext

let ctx: AudioContext | null = null

function getContext(): AudioContext | null {
  if (ctx) return ctx
  const Ctor: AudioContextCtor | undefined =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: AudioContextCtor }).webkitAudioContext
  if (!Ctor) return null
  try {
    ctx = new Ctor()
  } catch {
    return null
  }
  return ctx
}

export function unlockBeep(): void {
  const c = getContext()
  if (!c) return
  if (c.state === 'suspended') c.resume().catch(() => {})
  try {
    const src = c.createBufferSource()
    src.buffer = c.createBuffer(1, 1, 22050)
    src.connect(c.destination)
    src.start(0)
  } catch (err) {
    console.warn('Звук недоступен:', err)
  }
}

export function beep(final = false): void {
  const c = getContext()
  if (!c || c.state !== 'running') return
  try {
    const now = c.currentTime
    const duration = final ? 0.35 : 0.15
    const osc = c.createOscillator()
    const gain = c.createGain()
    osc.type = 'sine'
    osc.frequency.value = final ? 880 : 660
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(0.25, now + 0.01)
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration)
    osc.connect(gain)
    gain.connect(c.destination)
    osc.start(now)
    osc.stop(now + duration)
  } catch (err) {
    console.warn('Звук недоступен:', err)
  }
}
