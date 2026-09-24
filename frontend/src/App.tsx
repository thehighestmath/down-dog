import { useState, useEffect } from 'react'
import './App.css'

interface Pose {
  "Название": string;
  "Категория": string;
  "Сложность (1-4)": number;
  "Фокус (группы мышц)": string;
  "Полный цикл, сек": number;
  [key: string]: any;
}

interface Workout {
  id: string;
  duration_min: number;
  level: string;
  focus: string;
  poses: string[];
}

function App() {
  const [poses, setPoses] = useState<Pose[]>([])
  const [durationMin, setDurationMin] = useState<number>(15)
  const [level, setLevel] = useState<string>('beginner')
  const [focus, setFocus] = useState<string>('full_body')
  const [generatedWorkout, setGeneratedWorkout] = useState<Workout | null>(null)
  const [foundWorkout, setFoundWorkout] = useState<Workout | null>(null)
  const [searchId, setSearchId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API_URL = 'http://localhost:8000/api'

  useEffect(() => {
    const fetchPoses = async () => {
      try {
        const response = await fetch(`${API_URL}/poses`)
        if (!response.ok) throw new Error('Ошибка загрузки поз')
        const data = await response.json()
        setPoses(data)
      } catch (err: any) {
        console.error(err)
        setError("Не удалось загрузить позы. Проверьте, запущен ли FastAPI.")
      }
    }
    fetchPoses()
  }, [])

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setGeneratedWorkout(null)

    try {
      const response = await fetch(`${API_URL}/workouts/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_min: Number(durationMin), level, focus })
      })
      if (!response.ok) {
        const errData = await response.json().catch(() => null)
        throw new Error(errData?.detail || 'Ошибка при генерации тренировки')
      }
      const data = await response.json()
      setGeneratedWorkout(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchId.trim()) return
    setLoading(true)
    setError(null)
    setFoundWorkout(null)

    try {
      const response = await fetch(`${API_URL}/workouts/${searchId}`)
      if (!response.ok) throw new Error("Тренировка с таким ID не найдена")
      const data = await response.json()
      setFoundWorkout(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Общий стиль для карточек, чтобы текст был читаемым на фоне картинки
  const cardStyle = {
    marginBottom: '30px',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.92)', // Полупрозрачный белый фон
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)' // Легкая тень для объема
  };

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'sans-serif', 
      maxWidth: '900px', 
      margin: '0 auto', 
      color: '#333',
      minHeight: '100vh',
      // 👇 Добавляем фоновую картинку
      backgroundImage: 'url("/bg.jpg")', 
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundAttachment: 'fixed'
    }}>
      <h1 style={{ textAlign: 'center', color: '#fff', textShadow: '2px 2px 4px rgba(0,0,0,0.7)' }}>
        🧘‍♂️ Генератор Йога-тренировок
      </h1>
      
      {error && (
        <div style={{ color: '#d32f2f', padding: '15px', background: 'rgba(255, 235, 238, 0.95)', borderRadius: '8px', marginBottom: '20px', fontWeight: 'bold' }}>
          {error}
        </div>
      )}

      {/* --- Блок 1: Доступные позы --- */}
      <section style={cardStyle}>
        <h2 style={{ color: '#333', marginTop: 0 }}>📚 База поз ({poses.length} шт.)</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '10px', maxHeight: '300px', overflowY: 'auto' }}>
          {poses.map((pose, idx) => (
            <div key={idx} style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '5px', background: 'white' }}>
              <strong>{pose["Название"]}</strong>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                Сложность: {pose["Сложность (1-4)"]} | Время: {pose["Полный цикл, сек"]} сек
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* --- Блок 2: Форма генерации --- */}
      <section style={cardStyle}>
        <h2 style={{ color: '#333', marginTop: 0 }}>⚙️ Сгенерировать тренировку</h2>
        <form onSubmit={handleGenerate} style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {/* 👇 Сделали подписи жирными и темными */}
            <label style={{ fontWeight: 'bold', color: '#333' }}>Фокус:</label>
            <select value={focus} onChange={(e) => setFocus(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
              <option value="back">Спина (back)</option>
              <option value="neck">Шея (neck)</option>
              <option value="legs">Ноги (legs)</option>
              <option value="full_body">Все тело (full_body)</option>
              <option value="relaxation">Расслабление (relaxation)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold', color: '#333' }}>Уровень:</label>
            <select value={level} onChange={(e) => setLevel(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
              <option value="beginner">Новичок (beginner)</option>
              <option value="intermediate">Средний (intermediate)</option>
              <option value="advanced">Продвинутый (advanced)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold', color: '#333' }}>Длительность (мин):</label>
            <select value={durationMin} onChange={(e) => setDurationMin(Number(e.target.value))} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}>
              <option value={5}>5 минут</option>
              <option value={10}>10 минут</option>
              <option value={15}>15 минут</option>
              <option value={20}>20 минут</option>
              <option value={30}>30 минут</option>
            </select>
          </div>

          <button type="submit" disabled={loading} style={{ padding: '10px 20px', background: '#646cff', color: 'white', border: 'none', borderRadius: '5px', cursor: loading ? 'not-allowed' : 'pointer', height: '40px', fontWeight: 'bold' }}>
            {loading ? 'Генерация...' : 'Сгенерировать'}
          </button>
        </form>
      </section>

      {/* --- Блок 3: Результат генерации --- */}
      {generatedWorkout && (
        <section style={{ ...cardStyle, border: '2px solid #4caf50', background: 'rgba(232, 245, 233, 0.95)' }}>
          {/* 👇 Заголовок теперь темно-зеленый, а не белый */}
          <h2 style={{ color: '#2e7d32', marginTop: 0 }}>✅ Тренировка готова!</h2>
          
          {/* 👇 ИСПРАВЛЕН БЛОК С ID: серый фон, красный жирный текст */}
          <p>
            <strong>ID тренировки:</strong>{' '}
            <code style={{ 
              background: '#e0e0e0', 
              color: '#d32f2f', 
              padding: '4px 8px', 
              borderRadius: '4px', 
              fontWeight: 'bold',
              fontSize: '16px'
            }}>
              {generatedWorkout.id}
            </code>
          </p>
          
          <p><strong>Параметры:</strong> {generatedWorkout.level} | {generatedWorkout.focus} | {generatedWorkout.duration_min} мин.</p>
          
          <h3 style={{ color: '#333' }}>Список поз:</h3>
          {generatedWorkout.poses.length > 0 ? (
            <ol style={{ lineHeight: '1.6', color: '#333' }}>
              {generatedWorkout.poses.map((poseName, idx) => (
                <li key={idx}>{poseName}</li>
              ))}
            </ol>
          ) : (
            <p style={{ color: '#d32f2f' }}>Не удалось подобрать позы под эти параметры.</p>
          )}

          <button 
            onClick={() => setSearchId(generatedWorkout.id)}
            style={{ marginTop: '15px', padding: '8px 16px', background: '#2196f3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Вставить ID в поиск ↓
          </button>
        </section>
      )}

      {/* --- Блок 4: Поиск по ID --- */}
      <section style={cardStyle}>
        <h2 style={{ color: '#333', marginTop: 0 }}>🔍 Найти тренировку по ID</h2>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            value={searchId} 
            onChange={(e) => setSearchId(e.target.value)} 
            placeholder="Введите UUID тренировки"
            style={{ padding: '8px', flex: 1, borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <button type="submit" disabled={loading} style={{ padding: '8px 16px', cursor: 'pointer', background: '#333', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}>
            Найти
          </button>
        </form>

        {foundWorkout && (
          <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(227, 242, 253, 0.95)', borderRadius: '8px', border: '1px solid #90caf9' }}>
            <h3 style={{ color: '#1565c0', marginTop: 0 }}>Найдена тренировка:</h3>
            <p><strong>ID:</strong> {foundWorkout.id}</p>
            <p><strong>Уровень:</strong> {foundWorkout.level}</p>
            <p><strong>Фокус:</strong> {foundWorkout.focus}</p>
            <p><strong>Длительность:</strong> {foundWorkout.duration_min} мин.</p>
            <p><strong>Позы:</strong></p>
            <ul style={{ color: '#333' }}>
              {foundWorkout.poses.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </div>
        )}
      </section>
    </div>
  )
}

export default App