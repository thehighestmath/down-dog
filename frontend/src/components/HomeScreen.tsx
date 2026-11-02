import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { DURATIONS, FOCUS_OPTIONS, LEVEL_OPTIONS } from '../constants'
import type { Pose, Workout } from '../types'
import { btnStyle } from '../utils/styles'
import './HomeScreen.css'

interface HomeScreenProps {
  poses: Pose[]
  durationMin: number
  setDurationMin: (v: number) => void
  level: string
  setLevel: (v: string) => void
  focus: string
  setFocus: (v: string) => void
  generatedWorkout: Workout | null
  foundWorkout: Workout | null
  searchId: string
  setSearchId: (v: string) => void
  loading: boolean
  error: string | null
  onGenerate: (e: FormEvent) => void
  onSearch: (e: FormEvent) => void
  onStartWorkout: (w: Workout) => void
}

export function HomeScreen({
  poses,
  durationMin,
  setDurationMin,
  level,
  setLevel,
  focus,
  setFocus,
  generatedWorkout,
  foundWorkout,
  searchId,
  setSearchId,
  loading,
  error,
  onGenerate,
  onSearch,
  onStartWorkout,
}: HomeScreenProps) {
  // Показывать предупреждение, пока оно не было увидено раньше
  const [showWarning] = useState(() => {
    try {
      return localStorage.getItem('healthWarningSeen') !== '1'
    } catch {
      return true
    }
  })

  // Помечаем как просмотренное, когда блок с тренировкой реально появился
  useEffect(() => {
    if (!generatedWorkout || !showWarning) return
    try {
      localStorage.setItem('healthWarningSeen', '1')
    } catch {
      // localStorage недоступен (например, приватный режим), игнорируем
    }
  }, [generatedWorkout, showWarning])

  return (
    <div className="home">
      <div className="home__bg" aria-hidden="true" />
      <h1 className="home__title">🧘‍♂️ Генератор Йога-тренировок</h1>

      {error && <div className="home__error">{error}</div>}

      <section className="home__card">
        <h2 className="home__card-title">📚 База поз ({poses.length} шт.)</h2>
        <div className="home__pose-grid">
          {poses.map((pose) => (
            <div key={pose.id} className="home__pose-item">
              <strong>{pose.name_en}</strong>
              {pose.name_ru && <div className="home__pose-name-ru">{pose.name_ru}</div>}
              <div className="home__pose-meta">
                Сложность: {pose.difficulty} | Цикл: {pose.full_cycle_sec ?? '—'} сек
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="home__card">
        <h2 className="home__card-title">⚙️ Сгенерировать тренировку</h2>
        <form onSubmit={onGenerate} className="home__form">
          <div className="home__field">
            <label className="home__label">Фокус:</label>
            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              className="home__input"
            >
              {FOCUS_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="home__field">
            <label className="home__label">Уровень:</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="home__input"
            >
              {LEVEL_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="home__field">
            <label className="home__label">Длительность (мин):</label>
            <select
              value={durationMin}
              onChange={(e) => setDurationMin(Number(e.target.value))}
              className="home__input"
            >
              {DURATIONS.map((min) => (
                <option key={min} value={min}>
                  {min} минут
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="home__submit"
            style={btnStyle('#646cff')}
          >
            {loading ? 'Генерация...' : 'Сгенерировать'}
          </button>
        </form>
      </section>

      {generatedWorkout && (
        <section className="home__card home__card--generated">
          <h2 className="home__card-title home__card-title--success">
            ✅ Тренировка готова!
          </h2>
          <p>
            <strong>ID:</strong> <code className="home__id">{generatedWorkout.id}</code>
          </p>
          <p>
            <strong>Параметры:</strong> {generatedWorkout.level} |{' '}
            {generatedWorkout.focus} | {generatedWorkout.duration_min} мин.
          </p>
          <h3>Список поз:</h3>
          <ol className="home__pose-list">
            {generatedWorkout.poses.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ol>
          <div className="home__actions">
            <button
              onClick={() => onStartWorkout(generatedWorkout)}
              style={btnStyle('#2e7d32')}
            >
              ▶ Начать тренировку
            </button>
            <button
              onClick={() => setSearchId(generatedWorkout.id)}
              style={btnStyle('#2196f3')}
            >
              Вставить ID в поиск ↓
            </button>
            {showWarning && (
              <h2 className="home__warning">
                ❌При травмах и заболеваниях нужно проконсультироваться с врачом!
              </h2>
            )}
          </div>
        </section>
      )}

      <section className="home__card">
        <h2 className="home__card-title">🔍 Найти тренировку по ID</h2>
        <form onSubmit={onSearch} className="home__search-form">
          <input
            type="text"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            placeholder="Введите UUID тренировки"
            className="home__input home__search-input"
          />
          <button type="submit" disabled={loading} style={btnStyle('#333')}>
            Найти
          </button>
        </form>

        {foundWorkout && (
          <div className="home__found">
            <h3 className="home__found-title">Найдена тренировка:</h3>
            <p className="home__found-id">
              <strong>ID:</strong> {foundWorkout.id}
            </p>
            <p>
              <strong>Уровень:</strong> {foundWorkout.level}
            </p>
            <p>
              <strong>Фокус:</strong> {foundWorkout.focus}
            </p>
            <p>
              <strong>Длительность:</strong> {foundWorkout.duration_min} мин.
            </p>
            <ul>
              {foundWorkout.poses.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
            <button
              onClick={() => onStartWorkout(foundWorkout)}
              style={btnStyle('#2e7d32')}
            >
              ▶ Начать тренировку
            </button>
          </div>
        )}
      </section>
    </div>
  )
}
