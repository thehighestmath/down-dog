import type { CSSProperties } from 'react'
import type { Workout } from '../types'
import { btnStyle } from '../utils/styles'

interface FinishedScreenProps {
  workout: Workout
  onHome: () => void
  onRepeat: () => void
}

export function FinishedScreen({ workout, onHome, onRepeat }: FinishedScreenProps) {
  // Кнопки одинаковой ширины: раскладка не зависит от подписей
  const actionBtn = (color: string): CSSProperties => ({
    ...btnStyle(color),
    width: '100%',
    minHeight: '44px',
    padding: '0 8px',
    fontSize: '15px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  })

  return (
    <div
      style={{
        // Привязан к видимой области экрана: не зависит от отступов родителей и не прокручивается
        position: 'fixed',
        inset: 0,
        overflowY: 'auto', // только на очень низких экранах (например, ландшафт)
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg,#1b5e20,#2e7d32)',
        color: '#fff',
        padding: 'clamp(16px, 5vw, 32px)',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '64px', lineHeight: 1.1 }}>🎉</div>
      <h1
        style={{
          margin: '8px 0 0',
          fontSize: 'clamp(20px, 7vw, 32px)',
          lineHeight: 1.2,
        }}
      >
        Тренировка завершена!
      </h1>

      {/* Параметры: всегда место под две строки, длинный текст обрезается */}
      <div
        style={{
          width: '100%',
          height: '2.8em',
          marginTop: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          lineHeight: 1.4,
          opacity: 0.85,
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
          {workout.duration_min} мин · {workout.level} · {workout.focus}
        </span>
      </div>

      <p style={{ margin: '4px 0 0', opacity: 0.7, fontSize: '14px', lineHeight: 1.4 }}>
        Поз в практике: {workout.poses.length}
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
          gap: '12px',
          width: '100%',
          maxWidth: '360px',
          marginTop: '24px',
        }}
      >
        <button onClick={onRepeat} style={actionBtn('#4caf50')}>
          🔁 Повторить
        </button>
        <button onClick={onHome} style={actionBtn('#455a64')}>
          🏠 На главную
        </button>
      </div>
    </div>
  )
}
