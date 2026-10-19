import { useEffect, useState, type FormEvent } from 'react'
import './App.css'
import { fetchPoses, generateWorkout, getWorkoutById } from './api'
import { FinishedScreen } from './components/FinishedScreen'
import { HomeScreen } from './components/HomeScreen'
import { Player } from './components/Player'
import type { Pose, View, Workout } from './types'

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
    fetchPoses()
      .then(setPoses)
      .catch((err) => {
        console.error(err)
        setError('Не удалось загрузить позы. Проверьте, запущен ли бэкенд.')
      })
  }, [])

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setGeneratedWorkout(null)
    try {
      const workout = await generateWorkout({
        duration_min: Number(durationMin),
        level,
        focus,
      })
      setGeneratedWorkout(workout)
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
      const workout = await getWorkoutById(searchId)
      setFoundWorkout(workout)
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

  return (
    <HomeScreen
      poses={poses}
      durationMin={durationMin}
      setDurationMin={setDurationMin}
      level={level}
      setLevel={setLevel}
      focus={focus}
      setFocus={setFocus}
      generatedWorkout={generatedWorkout}
      foundWorkout={foundWorkout}
      searchId={searchId}
      setSearchId={setSearchId}
      loading={loading}
      error={error}
      onGenerate={handleGenerate}
      onSearch={handleSearch}
      onStartWorkout={startWorkout}
    />
  )
}

export default App
