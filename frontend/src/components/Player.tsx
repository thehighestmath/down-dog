import { useEffect, useMemo, useRef, useState } from 'react'
import { trackPoseViewed } from '../analytics'
import type { PlaylistItem, Pose, Workout } from '../types'
import { btnStyle } from '../utils/styles'
import { useWakeLock } from '../useWakeLock'
import { beep, unlockBeep } from '../beep'
import { AudioLang, AudioQueue, Phrase, phraseUrl, poseIntroUrls } from '../audio'
import styles from './Player.module.css'

const LANG = AudioLang.Ru
const BEEP_SECONDS = 3

interface PlayerProps {
  workout: Workout
  poses: Pose[]
  onStop: (poseIndex?: number) => void
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
  const prevPoseIdx = useRef(-1)
  const [audio] = useState(() => new AudioQueue())

  // Очередь озвучки: один экземпляр на время тренировки
  useEffect(() => () => audio.stop(), [audio])

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

  // Завершение: останавливаем очередь и озвучиваем финальную фразу
  useEffect(() => {
    if (totalSec > 0 && elapsed >= totalSec && !finishedRef.current) {
      finishedRef.current = true
      setRunning(false)
      audio.stop()
      new Audio(phraseUrl(LANG, Phrase.Finish)).play().catch(() => {})
      onFinish()
    }
  }, [elapsed, totalSec, onFinish, audio])

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

  // Трекинг смены позы
  useEffect(() => {
    if (currentIdx !== prevPoseIdx.current && current) {
      prevPoseIdx.current = currentIdx
      trackPoseViewed(workout.id, current.name, currentIdx)
    }
  }, [currentIdx, current, workout.id])

  const isLastPose = currentIdx === playlist.length - 1

  const lastBeepRef = useRef('')
  useEffect(() => {
    if (!running || finishedRef.current) return
    if (timeLeft < 1 || timeLeft > BEEP_SECONDS) return
    const key = `${currentIdx}:${timeLeft}`
    if (lastBeepRef.current === key) return
    lastBeepRef.current = key
    beep(timeLeft === 1)
  }, [timeLeft, currentIdx, running])

  const handleSkip = () => {
    if (isLastPose) {
      onStop(currentIdx)
      return
    }
    const nextStart = poseOffsets[currentIdx + 1] ?? totalSec
    baseMsRef.current = nextStart * 1000
    resumedAtRef.current = Date.now()
    setElapsed(nextStart)
  }

  if (!current || !workout?.poses || workout.poses.length === 0) {
    return (
      <div className={styles.emptyContainer}>
        <div className={styles.emptyTitle}>Тренировка пуста</div>
        <div className={styles.emptyText}>
          Не удалось найти упражнения для этой тренировки. Пожалуйста, вернитесь назад и
          измените параметры.
        </div>
        <button onClick={() => onStop()} style={btnStyle('#444')}>
          Вернуться назад
        </button>
      </div>
    )
  }

  const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const ss = String(timeLeft % 60).padStart(2, '0')
  const nextPose = playlist[currentIdx + 1]?.pose
  const contraindications = current.pose?.contraindications?.trim()

  return (
    <div className={styles.container}>
      <div className={styles.headerRow}>
        <div className={styles.poseCounter}>
          Поза {currentIdx + 1} / {playlist.length}
        </div>
        <div className={styles.buttonGroup}>
          <button
            onClick={() => {
              unlockBeep()
              setRunning((r) => !r)
            }}
            style={btnStyle('#444')}
          >
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

      <div className={styles.progressBarContainer}>
        <div
          className={styles.progressBarFill}
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      <div className={styles.imageWrapper}>
        {current.pose?.image_url ? (
          <img
            className={styles.poseImage}
            src={current.pose.image_url}
            alt={current.pose?.name_en || current.name}
            loading="eager"
            decoding="async"
          />
        ) : (
          <div className={styles.imagePlaceholder}>Изображение недоступно</div>
        )}
      </div>

      <div className={styles.titlesContainer}>
        <div className={styles.poseTitleRu}>
          {current.pose?.name_ru || current.name}
        </div>
        {current.pose?.name_sanskrit && (
          <div className={styles.poseTitleSub}>
            {current.pose.name_sanskrit} · {current.pose.name_en}
          </div>
        )}
      </div>

      <div
        className={styles.timer}
        style={{ color: timeLeft <= 3 ? '#ff5252' : '#fff' }}
      >
        {mm}:{ss}
      </div>

      <div className={styles.nextPose}>
        {nextPose ? `Далее: ${nextPose.name_ru || nextPose.name_en}` : '\u00a0'}
      </div>

      {current.pose?.description && (
        <div className={styles.descriptionBox}>{current.pose.description}</div>
      )}

      {contraindications && contraindications.toLowerCase() !== 'отсутствуют' && (
        <div className={styles.contraindicationsBox}>
          <div className={styles.contraindicationsTitle}>⚠ Противопоказания</div>
          {contraindications}
        </div>
      )}

      {confirmStop && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
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
