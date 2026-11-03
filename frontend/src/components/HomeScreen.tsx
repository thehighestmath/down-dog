import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { DURATIONS, FOCUS_OPTIONS, LEVEL_OPTIONS } from '../constants'
import type { Pose, Workout } from '../types'
import { btnStyle } from '../utils/styles'
import styles from './HomeScreen.module.css'

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

  const isPosesEmpty = !generatedWorkout?.poses || generatedWorkout.poses.length === 0

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.title}>🧘‍♂️ Генератор Йога-тренировок</h1>

      {error && <div className={styles.errorBox}>{error}</div>}

      <section className={styles.card}>
        <h2 className={styles.cardHeading}>📚 База поз ({poses.length} шт.)</h2>
        <div className={styles.posesGrid}>
          {poses.map((pose) => (
            <div key={pose.id} className={styles.poseItem}>
              <strong>{pose.name_en}</strong>
              {pose.name_ru && <div className={styles.poseNameRu}>{pose.name_ru}</div>}
              <div className={styles.poseMeta}>
                Сложность: {pose.difficulty} | Цикл: {pose.full_cycle_sec ?? '—'} сек
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.card}>
        <h2 className={styles.cardHeading}>⚙️ Сгенерировать тренировку</h2>
        <form onSubmit={onGenerate} className={styles.generateForm}>
          <div className={styles.formRow}>
            <label className={styles.formLabel}>Фокус:</label>
            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              className={styles.formSelect}
            >
              {FOCUS_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.formRow}>
            <label className={styles.formLabel}>Уровень:</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className={styles.formSelect}
            >
              {LEVEL_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.formRow}>
            <label className={styles.formLabel}>Длительность (мин):</label>
            <select
              value={durationMin}
              onChange={(e) => setDurationMin(Number(e.target.value))}
              className={styles.formSelect}
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
            className={styles.submitButton}
            style={btnStyle('#646cff')}
          >
            {loading ? 'Генерация...' : 'Сгенерировать'}
          </button>
        </form>
      </section>

      {generatedWorkout && (
        <section className={styles.cardGenerated}>
          <h2 className={styles.successHeading}>✅ Тренировка готова!</h2>
          <p>
            <strong>ID:</strong>{' '}
            <code className={styles.idCode}>{generatedWorkout.id}</code>
          </p>
          <p>
            <strong>Параметры:</strong> {generatedWorkout.level} |{' '}
            {generatedWorkout.focus} | {generatedWorkout.duration_min} мин.
          </p>
          <h3>Список поз:</h3>
          <ol className={styles.poseList}>
            {generatedWorkout.poses.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ol>
          <div className={styles.buttonGroup}>
            <button
              onClick={() => onStartWorkout(generatedWorkout)}
              disabled={isPosesEmpty}
              style={{
                ...btnStyle('#2e7d32'),
                opacity: isPosesEmpty ? 0.5 : 1,
                cursor: isPosesEmpty ? 'not-allowed' : 'pointer',
              }}
            >
              {isPosesEmpty ? '⚠️ Нет доступных поз' : '▶ Начать тренировку'}
            </button>
            <button
              onClick={() => setSearchId(generatedWorkout.id)}
              style={btnStyle('#2196f3')}
            >
              Вставить ID в поиск ↓
            </button>
            {showWarning && (
              <h2 className={styles.warningText}>
                ❌ При травмах и заболеваниях нужно проконсультироваться с врачом!
              </h2>
            )}
          </div>
        </section>
      )}

      <section className={styles.card}>
        <h2 className={styles.cardHeading}>🔍 Найти тренировку по ID</h2>
        <form onSubmit={onSearch} className={styles.searchForm}>
          <input
            type="text"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            placeholder="Введите UUID тренировки"
            className={styles.searchInput}
          />
          <button type="submit" disabled={loading} style={btnStyle('#333')}>
            Найти
          </button>
        </form>

        {foundWorkout && (
          <div className={styles.cardFound}>
            <h3 className={styles.foundHeading}>Найдена тренировка:</h3>
            <p>
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
