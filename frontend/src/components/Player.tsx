import { useEffect, useMemo, useRef, useState } from 'react'
import { trackPoseViewed } from '../analytics'
import type { PlaylistItem, Pose, Workout } from '../types'
import { btnStyle } from '../utils/styles'

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
  const prevPoseIdx = useRef(-1)

  // Тик таймера
  useEffect(() => {
    if (!running || totalSec === 0) return
    const id = window.setInterval(() => {
      setElapsed((e) => Math.min(e + 1, totalSec))
    }, 1000)
    return () => window.clearInterval(id)
  }, [running, totalSec])

  // Завершение
  useEffect(() => {
    if (totalSec > 0 && elapsed >= totalSec && !finishedRef.current) {
      finishedRef.current = true
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

  const current = playlist[currentIdx]
  const timeLeft = current ? Math.max(0, current.duration - timeInPose) : 0
  const progress = totalSec > 0 ? elapsed / totalSec : 0

  // Трекинг смены позы
  useEffect(() => {
    if (currentIdx !== prevPoseIdx.current && current) {
      prevPoseIdx.current = currentIdx
      trackPoseViewed(workout.id, current.name, currentIdx)
    }
  }, [currentIdx, current, workout.id])

  // Пропустить текущую позу
  const handleSkip = () => {
    const nextStart = poseOffsets[currentIdx + 1] ?? totalSec
    setElapsed(nextStart)
  }

  if (!current) return null

  const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const ss = String(timeLeft % 60).padStart(2, '0')
  const nextPose = playlist[currentIdx + 1]?.pose
  const isLastPose = currentIdx === playlist.length - 1

  const imgSrc = current.pose?.image_url
    ? current.pose.image_url.startsWith('http')
      ? current.pose.image_url
      : current.pose.image_url
    : null

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#111',
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px',
        boxSizing: 'border-box',
        maxWidth: '900px',
        margin: '0 auto',
      }}
    >
      {/* Верхняя строка */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ fontSize: '14px', opacity: 0.7 }}>
          Поза {currentIdx + 1} / {playlist.length}
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button onClick={() => setRunning((r) => !r)} style={btnStyle('#444')}>
            {running ? '⏸ Пауза' : '▶ Продолжить'}
          </button>
          <button
            onClick={handleSkip}
            style={btnStyle('#ff9800')}
            title={isLastPose ? 'Завершить тренировку' : 'Пропустить позу'}
          >
            {isLastPose ? '⏭ Завершить' : '⏭ Пропустить'}
          </button>
          <button onClick={() => setConfirmStop(true)} style={btnStyle('#c62828')}>
            ⏹ Стоп
          </button>
        </div>
      </div>

      {/* Прогресс тренировки */}
      <div
        style={{
          height: '6px',
          background: '#333',
          borderRadius: '3px',
          marginTop: '14px',
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

      {/* Картинка позы */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          margin: '24px 0',
          minHeight: '260px',
        }}
      >
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={current.pose?.name_en || current.name}
            loading="eager"
            decoding="async"
            style={{
              maxWidth: '100%',
              maxHeight: '420px',
              borderRadius: '12px',
              objectFit: 'contain',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          />
        ) : (
          <div style={{ fontSize: '14px', opacity: 0.5 }}>Изображение недоступно</div>
        )}
      </div>

      {/* Названия */}
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '32px', fontWeight: 700, lineHeight: 1.2 }}>
          {current.pose?.name_ru || current.name}
        </div>
        {current.pose?.name_sanskrit && (
          <div style={{ fontSize: '16px', opacity: 0.7, marginTop: '6px' }}>
            {current.pose.name_sanskrit} · {current.pose.name_en}
          </div>
        )}
      </div>

      {/* Таймер */}
      <div
        style={{
          textAlign: 'center',
          marginTop: '16px',
          fontSize: '72px',
          fontVariantNumeric: 'tabular-nums',
          fontWeight: 800,
          color: timeLeft <= 3 ? '#ff5252' : '#fff',
          transition: 'color 0.2s',
        }}
      >
        {mm}:{ss}
      </div>

      {/* Описание */}
      {current.pose?.description && (
        <div
          style={{
            background: 'rgba(255,255,255,0.08)',
            padding: '14px',
            borderRadius: '10px',
            fontSize: '15px',
            lineHeight: 1.5,
            marginTop: '12px',
            maxHeight: '260px',
            overflowY: 'auto',
          }}
        >
          {current.pose.description}
        </div>
      )}

      {nextPose && (
        <div
          style={{
            marginTop: '16px',
            textAlign: 'center',
            fontSize: '14px',
            opacity: 0.6,
          }}
        >
          Далее: {nextPose.name_ru || nextPose.name_en}
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
          }}
        >
          <div
            style={{
              background: '#222',
              padding: '24px',
              borderRadius: '12px',
              maxWidth: '360px',
              textAlign: 'center',
            }}
          >
            <p style={{ marginTop: 0 }}>Завершить тренировку досрочно?</p>
            <div
              style={{
                display: 'flex',
                gap: '10px',
                justifyContent: 'center',
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
