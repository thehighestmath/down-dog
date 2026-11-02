import { useEffect, useRef } from 'react'

export type WorkoutStatus = 'idle' | 'running' | 'paused' | 'stopped' | 'finished'

export function useWakeLock(active: boolean) {
  const sentinelRef = useRef<WakeLockSentinel | null>(null)

  useEffect(() => {
    if (!active || !('wakeLock' in navigator)) return

    let cancelled = false

    const acquire = async () => {
      // не запрашиваем повторно, если блокировка уже держится
      if (sentinelRef.current && !sentinelRef.current.released) return

      try {
        const sentinel = await navigator.wakeLock.request('screen')

        // эффект мог завершиться, пока шёл запрос
        if (cancelled) {
          await sentinel.release()
          return
        }

        sentinel.addEventListener('release', () => {
          if (sentinelRef.current === sentinel) sentinelRef.current = null
        })
        sentinelRef.current = sentinel
      } catch (err) {
        console.warn('Wake Lock не получен:', err)
      }
    }

    // браузер снял блокировку при скрытии страницы, берём заново при возврате
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') void acquire()
    }

    void acquire()
    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', onVisibilityChange)
      void sentinelRef.current?.release()
      sentinelRef.current = null
    }
  }, [active])
}
