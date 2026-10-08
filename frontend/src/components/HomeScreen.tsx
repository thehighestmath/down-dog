import type { CSSProperties, FormEvent } from 'react'
import { DURATIONS, FOCUS_OPTIONS, LEVEL_OPTIONS } from '../constants'
import type { Pose, Workout } from '../types'
import { btnStyle } from '../utils/styles'

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
  const cardStyle: CSSProperties = {
    marginBottom: '24px',
    padding: '20px',
    background: 'rgba(255,255,255,0.92)',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
  }

  return (
    <div
      style={{
        padding: '20px',
        fontFamily: 'sans-serif',
        maxWidth: '900px',
        margin: '0 auto',
        color: '#333',
        minHeight: '100vh',
        backgroundImage: 'url("/bg.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
      }}
    >
      <h1
        style={{
          textAlign: 'center',
          color: '#fff',
          textShadow: '2px 2px 4px rgba(0,0,0,0.7)',
        }}
      >
        🧘‍♂️ Генератор Йога-тренировок
      </h1>

      {error && (
        <div
          style={{
            color: '#d32f2f',
            padding: '15px',
            background: 'rgba(255,235,238,0.95)',
            borderRadius: '8px',
            marginBottom: '20px',
            fontWeight: 'bold',
          }}
        >
          {error}
        </div>
      )}

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>📚 База поз ({poses.length} шт.)</h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: '10px',
            maxHeight: '300px',
            overflowY: 'auto',
          }}
        >
          {poses.map((pose) => (
            <div
              key={pose.id}
              style={{
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                background: 'white',
              }}
            >
              <strong>{pose.name_en}</strong>
              {pose.name_ru && (
                <div style={{ fontSize: '11px', color: '#888' }}>{pose.name_ru}</div>
              )}
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                Сложность: {pose.difficulty} | Цикл: {pose.full_cycle_sec ?? '—'} сек
              </div>
            </div>
          ))}
        </div>
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>⚙️ Сгенерировать тренировку</h2>
        <form
          onSubmit={onGenerate}
          style={{
            display: 'flex',
            gap: '15px',
            flexWrap: 'wrap',
            alignItems: 'flex-end',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Фокус:</label>
            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              style={{ padding: '8px', borderRadius: 4, border: '1px solid #ccc' }}
            >
              {FOCUS_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Уровень:</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              style={{ padding: '8px', borderRadius: 4, border: '1px solid #ccc' }}
            >
              {LEVEL_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Длительность (мин):</label>
            <select
              value={durationMin}
              onChange={(e) => setDurationMin(Number(e.target.value))}
              style={{ padding: '8px', borderRadius: 4, border: '1px solid #ccc' }}
            >
              {DURATIONS.map((min) => (
                <option key={min} value={min}>
                  {min} минут
                </option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={loading} style={btnStyle('#646cff')}>
            {loading ? 'Генерация...' : 'Сгенерировать'}
          </button>
        </form>
      </section>

      {generatedWorkout && (
        <section
          style={{
            ...cardStyle,
            border: '2px solid #4caf50',
            background: 'rgba(232,245,233,0.95)',
          }}
        >
          <h2 style={{ color: '#2e7d32', marginTop: 0 }}>✅ Тренировка готова!</h2>
          <p>
            <strong>ID:</strong>{' '}
            <code
              style={{
                background: '#e0e0e0',
                color: '#d32f2f',
                padding: '4px 8px',
                borderRadius: 4,
                fontWeight: 'bold',
              }}
            >
              {generatedWorkout.id}
            </code>
          </p>
          <p>
            <strong>Параметры:</strong> {generatedWorkout.level} |{' '}
            {generatedWorkout.focus} | {generatedWorkout.duration_min} мин.
          </p>
          <h3>Список поз:</h3>
          <ol style={{ lineHeight: 1.6 }}>
            {generatedWorkout.poses.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ol>
          <div
            style={{
              display: 'flex',
              gap: '10px',
              flexWrap: 'wrap',
              marginTop: '12px',
            }}
          >
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
          </div>
        </section>
      )}

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>🔍 Найти тренировку по ID</h2>
        <form onSubmit={onSearch} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            placeholder="Введите UUID тренировки"
            style={{
              padding: '8px',
              flex: 1,
              borderRadius: 4,
              border: '1px solid #ccc',
            }}
          />
          <button type="submit" disabled={loading} style={btnStyle('#333')}>
            Найти
          </button>
        </form>

        {foundWorkout && (
          <div
            style={{
              marginTop: '20px',
              padding: '15px',
              background: 'rgba(227,242,253,0.95)',
              borderRadius: 8,
              border: '1px solid #90caf9',
            }}
          >
            <h3 style={{ color: '#1565c0', marginTop: 0 }}>Найдена тренировка:</h3>
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
