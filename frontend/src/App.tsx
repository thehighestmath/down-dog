import { useState, useEffect, useMemo, useRef, type FormEvent } from 'react'
import './App.css'

interface Pose {
  id: number
  name_ru: string
  name_sanskrit: string | null
  name_en: string
  category: string
  difficulty: string
  focus_areas: string
  contraindications: string | null
  description: string | null
  image_url: string | null
  audio_url: string | null
  hold_time_sec: number | null
  full_cycle_sec: number | null
}

interface Workout {
  id: string
  duration_min: number
  level: string
  focus: string
  poses: string[]
}

type View = 'home' | 'player' | 'finished'

const FOCUS_OPTIONS = [
  { value: 'back', label: 'Спина (back)' },
  { value: 'neck', label: 'Шея (neck)' },
  { value: 'legs', label: 'Ноги (legs)' },
  { value: 'full_body', label: 'Все тело (full_body)' },
  { value: 'relaxation', label: 'Расслабление (relaxation)' },
]
const LEVEL_OPTIONS = [
  { value: 'beginner', label: 'Новичок (beginner)' },
  { value: 'intermediate', label: 'Средний (intermediate)' },
  { value: 'advanced', label: 'Продвинутый (advanced)' },
]
const DURATIONS = [5, 10, 15, 20, 30]

const API_URL = 'http://localhost:8000/api'

// ---------- Плеер тренировки ----------
interface PlaylistItem {
  name: string
  pose: Pose | undefined
  duration: number
}

function Player({
  workout,
  poses,
  onStop,
  onFinish,
}: {
  workout: Workout
  poses: Pose[]
  onStop: () => void
  onFinish: () => void
}) {
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

  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(true)
  const [confirmStop, setConfirmStop] = useState(false)
  const finishedRef = useRef(false)

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

  if (!current) return null

  const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const ss = String(timeLeft % 60).padStart(2, '0')
  const nextPose = playlist[currentIdx + 1]?.pose

  const imgSrc = current.pose?.image_url
    ? current.pose.image_url.startsWith('http')
      ? current.pose.image_url
      : `http://localhost:8000${current.pose.image_url}`
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
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => setRunning((r) => !r)} style={btnStyle('#444')}>
            {running ? '⏸ Пауза' : '▶ Продолжить'}
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
            transition: 'width 0.9s linear',
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

function btnStyle(bg: string): React.CSSProperties {
  return {
    background: bg,
    color: '#fff',
    border: 'none',
    padding: '10px 16px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
  }
}

// ---------- Экран завершения ----------
function FinishedScreen({
  workout,
  onHome,
  onRepeat,
}: {
  workout: Workout
  onHome: () => void
  onRepeat: () => void
}) {
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

// ---------- Основной App ----------
function App() {
  const [poses, setPoses] = useState<Pose[]>([])
  const [durationMin, setDurationMin] = useState(15)
  const [level, setLevel] = useState('beginner')
  const [focus, setFocus] = useState('full_body')
  const [generatedWorkout, setGeneratedWorkout] = useState<Workout | null>(null)
  const [foundWorkout, setFoundWorkout] = useState<Workout | null>(null)
  const [searchId, setSearchId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [view, setView] = useState<View>('home')
  const [activeWorkout, setActiveWorkout] = useState<Workout | null>(null)

  useEffect(() => {
    const fetchPoses = async () => {
      try {
        const r = await fetch(`${API_URL}/poses`)
        if (!r.ok) throw new Error('Ошибка загрузки поз')
        setPoses((await r.json()) as Pose[])
      } catch (err) {
        console.error(err)
        setError('Не удалось загрузить позы. Проверьте, запущен ли FastAPI.')
      }
    }
    fetchPoses()
  }, [])

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setGeneratedWorkout(null)
    try {
      const r = await fetch(`${API_URL}/workouts/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_min: Number(durationMin), level, focus }),
      })
      if (!r.ok) {
        const errData = (await r.json().catch(() => null)) as { detail?: string } | null
        throw new Error(errData?.detail || 'Ошибка при генерации тренировки')
      }
      setGeneratedWorkout((await r.json()) as Workout)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault()
    if (!searchId.trim()) return
    setLoading(true)
    setError(null)
    setFoundWorkout(null)
    try {
      const r = await fetch(`${API_URL}/workouts/${searchId}`)
      if (!r.ok) throw new Error('Тренировка с таким ID не найдена')
      setFoundWorkout((await r.json()) as Workout)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
    } finally {
      setLoading(false)
    }
  }

  const startWorkout = (w: Workout) => {
    setActiveWorkout(w)
    setView('player')
  }

  if (view === 'player' && activeWorkout) {
    return (
      <Player
        workout={activeWorkout}
        poses={poses}
        onStop={() => {
          setView('home')
          setActiveWorkout(null)
        }}
        onFinish={() => setView('finished')}
      />
    )
  }

  if (view === 'finished' && activeWorkout) {
    return (
      <FinishedScreen
        workout={activeWorkout}
        onHome={() => {
          setView('home')
          setActiveWorkout(null)
        }}
        onRepeat={() => setView('player')}
      />
    )
  }

  const cardStyle: React.CSSProperties = {
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

      {/* База поз */}
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

      {/* Генерация */}
      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>⚙️ Сгенерировать тренировку</h2>
        <form
          onSubmit={handleGenerate}
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

      {/* Результат генерации */}
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
              onClick={() => startWorkout(generatedWorkout)}
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

      {/* Поиск */}
      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>🔍 Найти тренировку по ID</h2>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
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
              onClick={() => startWorkout(foundWorkout)}
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

export default App
