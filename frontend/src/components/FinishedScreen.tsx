import type { Workout } from '../types'
import { btnStyle } from '../utils/styles'

interface FinishedScreenProps {
  workout: Workout
  onHome: () => void
  onRepeat: () => void
}

export function FinishedScreen({ workout, onHome, onRepeat }: FinishedScreenProps) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg,#1b5e20,#2e7d32)',
        color: '#fff',
        padding: '32px',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '64px' }}>🎉</div>
      <h1 style={{ marginTop: '8px' }}>Тренировка завершена!</h1>
      <p style={{ opacity: 0.85 }}>
        {workout.duration_min} мин · {workout.level} · {workout.focus}
      </p>
      <p style={{ opacity: 0.7, fontSize: '14px' }}>
        Поз в практике: {workout.poses.length}
      </p>
      <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
        <button onClick={onRepeat} style={btnStyle('#4caf50')}>
          🔁 Повторить
        </button>
        <button onClick={onHome} style={btnStyle('#455a64')}>
          🏠 На главную
        </button>
      </div>
    </div>
  )
}
