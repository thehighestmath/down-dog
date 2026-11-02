import type { Workout } from '../types'
import { btnStyle } from '../utils/styles'
import './FinishedScreen.css'

interface FinishedScreenProps {
  workout: Workout
  onHome: () => void
  onRepeat: () => void
}

export function FinishedScreen({ workout, onHome, onRepeat }: FinishedScreenProps) {
  return (
    <div className="finished">
      <div className="finished__emoji">🎉</div>
      <h1 className="finished__title">Тренировка завершена!</h1>

      <div className="finished__params">
        <span className="finished__params-text">
          {workout.duration_min} мин · {workout.level} · {workout.focus}
        </span>
      </div>

      <p className="finished__count">Поз в практике: {workout.poses.length}</p>

      <div className="finished__actions">
        <button
          onClick={onRepeat}
          className="finished__action-btn"
          style={btnStyle('#4caf50')}
        >
          🔁 Повторить
        </button>
        <button
          onClick={onHome}
          className="finished__action-btn"
          style={btnStyle('#455a64')}
        >
          🏠 На главную
        </button>
      </div>
    </div>
  )
}
