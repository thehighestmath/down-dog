import { API_URL } from './constants'
import type { Pose, Workout } from './types'

export async function fetchPoses(): Promise<Pose[]> {
  const r = await fetch(`${API_URL}/poses`)
  if (!r.ok) throw new Error('Ошибка загрузки поз')
  return (await r.json()) as Pose[]
}

export interface GenerateWorkoutParams {
  duration_min: number
  level: string
  focus: string
}

export async function generateWorkout(params: GenerateWorkoutParams): Promise<Workout> {
  const r = await fetch(`${API_URL}/workouts/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })

  if (!r.ok) {
    const errData = (await r.json().catch(() => null)) as { detail?: string } | null
    throw new Error(errData?.detail || 'Ошибка при генерации тренировки')
  }

  return (await r.json()) as Workout
}

export async function getWorkoutById(id: string): Promise<Workout> {
  const r = await fetch(`${API_URL}/workouts/${id}`)
  if (!r.ok) throw new Error('Тренировка с таким ID не найдена')
  return (await r.json()) as Workout
}