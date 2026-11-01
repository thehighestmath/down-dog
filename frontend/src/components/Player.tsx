import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { PlaylistItem, Pose, Workout } from '../types'
import { btnStyle } from '../utils/styles'
import { useWakeLock } from '../useWakeLock'
import { AudioLang, AudioQueue, Phrase, phraseUrl, poseIntroUrls } from '../audio'

const LANG: AudioLang = AudioLang.Ru

interface PlayerProps {
  workout: Workout
  poses: Pose[]
  onStop: () => void
  onFinish: () => void
}

export function Player({ workout, poses, onStop, onFinish }: PlayerProps) {
  const poseMap = useMemo(() => new Map(poses.map((p) => [p.name_en, p])), [poses])

  const playlist: PlaylistItem[] = useMemo(
    () =>
      workout.poses.map((name) => {
        const pose = poseMap.get(name)
        return {
          name,
          pose,
          duration: Math.max(5, pose?.full_cycle_sec ?? 30),
        }
      }),
    [workout, poseMap],
  )

  const totalSec = useMemo(
    () => playlist.reduce((s, x) => s + x.duration, 0),
    [playlist],
  )

  // Смещения начала каждой позы: [0, 30, 65, ...]
  const poseOffsets = useMemo(() => {
    const offsets: number[] = []
    let acc = 0
    for (const item of playlist) {
      offsets.push(acc)
      acc += item.duration
    }
    return offsets
  }, [playlist])

  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(true)
  const [confirmStop, setConfirmStop] = useState(false)
  const finishedRef = useRef(false)
  const baseMsRef = useRef(0)
  const resumedAtRef = useRef<number | null>(null)

  // Экран не гаснет, пока тренировка идёт (не на паузе)
  useWakeLock(running)

  // Очередь озвучки: один экземпляр на время тренировки
  const [audio] = useState(() => new AudioQueue())
  // При выходе с экрана (стоп, финиш) озвучка замолкает
  useEffect(() => () => audio.pause(), [audio])

  // Сохранение начала тренировки и обновление таймера
  useEffect(() => {
    if (!running || totalSec === 0) return
    resumedAtRef.current = Date.now()
    const update = () => {
      const ms = baseMsRef.current + (Date.now() - (resumedAtRef.current ?? Date.now()))
      setElapsed(Math.min(Math.floor(ms / 1000), totalSec))
    }

    const id = window.setInterval(update, 250)
    const onVisible = () => {
      if (document.visibilityState === 'visible') update()
    }
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      window.clearInterval(id)
      document.removeEventListener('visibilitychange', onVisible)
      baseMsRef.current += Date.now() - (resumedAtRef.current ?? Date.now())
    }
  }, [running, totalSec])

  // Завершение
  useEffect(() => {
    if (totalSec > 0 && elapsed >= totalSec && !finishedRef.current) {
      finishedRef.current = true
      setRunning(false)
      onFinish()
    }
  }, [elapsed, totalSec, onFinish])

  // Текущая поза
  let acc = 0
  let currentIdx = 0
  let timeInPose = 0
  for (let i = 0; i < playlist.length; i++) {
    const d = playlist[i].duration
    if (elapsed < acc + d) {
      currentIdx = i
      timeInPose = elapsed - acc
      break
    }
    acc += d
    if (i === playlist.length - 1) {
      currentIdx = i
      timeInPose = d
    }
  }

  // Озвучка: вступление к новой позе
  useEffect(() => {
    const item = playlist[currentIdx]
    if (!item || finishedRef.current) return
    audio.play(poseIntroUrls(item, currentIdx === 0, LANG))
  }, [currentIdx, playlist, audio])

  // Пауза и продолжение озвучки вместе с тренировкой
  useEffect(() => {
    if (running) audio.resume()
    else audio.pause()
  }, [running, audio])

  // Напоминание про дыхание на середине длинной позы
  const poseDuration = playlist[currentIdx]?.duration ?? 0
  useEffect(() => {
    if (running && poseDuration >= 30 && timeInPose === Math.floor(poseDuration / 2)) {
      audio.play([phraseUrl(LANG, Phrase.Breathe)])
    }
  }, [timeInPose, poseDuration, running, audio])

  const current = playlist[currentIdx]
  const timeLeft = current ? Math.max(0, current.duration - timeInPose) : 0
  const progress = totalSec > 0 ? elapsed / totalSec : 0

  // Пропустить текущую позу
  const handleSkip = () => {
    const nextStart = poseOffsets[currentIdx + 1] ?? totalSec
    baseMsRef.current = nextStart * 1000
    resumedAtRef.current = Date.now()
    setElapsed(nextStart)
  }

  if (!current) return null

  const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const ss = String(timeLeft % 60).padStart(2, '0')
  const nextPose = playlist[currentIdx + 1]?.pose
  const isLastPose = currentIdx === playlist.length - 1

  // Кнопки одинаковой ширины: смена подписи («Пауза» ↔ «Продолжить») не меняет раскладку
  const controlBtn = (color: string): CSSProperties => ({
    ...btnStyle(color),
    width: '100%',
    minHeight: '44px',
    padding: '0 4px',
    fontSize: '14px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  })

  const imgSrc = current.pose?.image_url
    ? current.pose.image_url.startsWith('http')
      ? current.pose.image_url
      : current.pose.image_url
    : null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        overflowY: 'auto', // прокрутка только на очень низких экранах (например, ландшафт)
        background: '#111',
        color: '#fff',
        padding: '0 clamp(12px, 4vw, 20px) clamp(12px, 4vw, 20px)',
        boxSizing: 'border-box',
        maxWidth: '900px',
        margin: '0 auto',
      }}
    >
      {/* Шапка закреплена сверху: кнопки всегда под рукой, пока читаешь описание */}
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 5,
          background: '#111',
          paddingTop: 'clamp(12px, 4vw, 20px)',
          paddingBottom: '8px',
        }}
      >
        <div
          style={{
            height: '1.4em',
            marginBottom: '6px',
            fontSize: '14px',
            lineHeight: 1.4,
            opacity: 0.7,
          }}
        >
          Поза {currentIdx + 1} / {playlist.length}
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
            gap: '8px',
          }}
        >
          <button onClick={() => setRunning((r) => !r)} style={controlBtn('#444')}>
            {running ? '⏸ Пауза' : '▶ Продолжить'}
          </button>
          <button
            onClick={handleSkip}
            style={controlBtn('#ff9800')}
            title={isLastPose ? 'Завершить тренировку' : 'Пропустить позу'}
          >
            {isLastPose ? '⏭ Завершить' : '⏭ Пропустить'}
          </button>
          <button onClick={() => setConfirmStop(true)} style={controlBtn('#c62828')}>
            ⏹ Стоп
          </button>
        </div>
        <div
          style={{
            height: '6px',
            background: '#333',
            borderRadius: '3px',
            marginTop: '10px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progress * 100}%`,
              background: 'linear-gradient(90deg,#4caf50,#8bc34a)',
              transition: 'width 0.3s linear',
            }}
          />
        </div>
      </div>

      {/* Картинка позы: фиксированная высота от высоты экрана */}
      <div
        style={{
          position: 'relative',
          height: 'min(32dvh, 320px)',
          minHeight: '140px',
          margin: '10px 0',
        }}
      >
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={current.pose?.name_en || current.name}
            loading="eager"
            decoding="async"
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              borderRadius: '12px',
            }}
          />
        ) : (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: '14px',
              opacity: 0.5,
            }}
          >
            Изображение недоступно
          </div>
        )}
      </div>

      {/* Названия: всегда место под две строки и строку санскрита */}
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            height: '2.4em',
            fontSize: 'clamp(20px, 6vw, 30px)',
            fontWeight: 700,
            lineHeight: 1.2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {current.pose?.name_ru || current.name}
          </span>
        </div>
        <div
          style={{
            height: '1.4em',
            marginTop: '2px',
            fontSize: '15px',
            lineHeight: 1.4,
            opacity: 0.7,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {current.pose?.name_sanskrit
            ? `${current.pose.name_sanskrit} · ${current.pose.name_en}`
            : '\u00a0'}
        </div>
      </div>

      {/* Таймер */}
      <div
        style={{
          textAlign: 'center',
          marginTop: '6px',
          fontSize: 'clamp(44px, 14vw, 72px)',
          lineHeight: 1.1,
          fontVariantNumeric: 'tabular-nums',
          fontWeight: 800,
          color: timeLeft <= 3 ? '#ff5252' : '#fff',
          transition: 'color 0.2s',
        }}
      >
        {mm}:{ss}
      </div>

      {/* Следующая поза: строка всегда занимает место */}
      <div
        style={{
          height: '1.4em',
          marginTop: '6px',
          textAlign: 'center',
          fontSize: '14px',
          lineHeight: 1.4,
          opacity: 0.6,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {nextPose ? `Далее: ${nextPose.name_ru || nextPose.name_en}` : '\u00a0'}
      </div>

      {/* Всё, что ниже, зависит от текста, но лежит под основным экраном и ничего не сдвигает */}
      {current.pose?.description && (
        <div
          style={{
            background: 'rgba(255,255,255,0.08)',
            padding: '14px',
            borderRadius: '10px',
            fontSize: '15px',
            lineHeight: 1.5,
            marginTop: '12px',
          }}
        >
          {current.pose.description}
        </div>
      )}

      {current.pose?.contraindications?.trim() &&
        current.pose.contraindications.trim().toLowerCase() !== 'отсутствуют' && (
          <div
            style={{
              background: 'rgba(198,40,40,0.15)',
              border: '1px solid rgba(198,40,40,0.4)',
              padding: '14px',
              borderRadius: '10px',
              fontSize: '15px',
              lineHeight: 1.5,
              marginTop: '12px',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: '6px' }}>
              ⚠ Противопоказания
            </div>
            {current.pose.contraindications}
          </div>
        )}

      {/* Подтверждение стопа */}
      {confirmStop && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 10,
            padding: '20px',
            boxSizing: 'border-box',
          }}
        >
          <div
            style={{
              background: '#222',
              padding: '24px',
              borderRadius: '12px',
              width: '100%',
              maxWidth: '360px',
              boxSizing: 'border-box',
              textAlign: 'center',
            }}
          >
            <p style={{ marginTop: 0 }}>Завершить тренировку досрочно?</p>
            <div
              style={{
                display: 'flex',
                gap: '10px',
                justifyContent: 'center',
                flexWrap: 'wrap',
                marginTop: '12px',
              }}
            >
              <button onClick={() => onStop()} style={btnStyle('#c62828')}>
                Да, стоп
              </button>
              <button onClick={() => setConfirmStop(false)} style={btnStyle('#444')}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
