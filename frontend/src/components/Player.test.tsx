import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pose, Workout } from '../types'
import { Player } from './Player'

// Звук, аналитика и wake lock в тестах не нужны: в jsdom их нет,
// а проверяем мы логику кнопок, а не браузерные API
vi.mock('../audio', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../audio')>()),
  AudioQueue: class {
    play() {}
    stop() {}
    pause() {}
    resume() {}
  },
}))
vi.mock('../beep', () => ({ beep: vi.fn(), unlockBeep: vi.fn() }))
vi.mock('../analytics', () => ({ trackPoseViewed: vi.fn() }))
vi.mock('../useWakeLock', () => ({ useWakeLock: vi.fn() }))

function makePose(id: number, nameEn: string): Pose {
  return {
    id,
    name_ru: `Поза ${id}`,
    name_sanskrit: null,
    name_en: nameEn,
    category: 'standing',
    difficulty: 'beginner',
    focus_areas: 'back',
    contraindications: null,
    description: null,
    image_url: null,
    audio_url: null,
    audio_name: nameEn,
    hold_time_sec: 30,
    full_cycle_sec: 30,
  }
}

const poses = [makePose(1, 'Mountain'), makePose(2, 'Tree')]
const workout: Workout = {
  id: 'w-1',
  duration_min: 1,
  level: 'beginner',
  focus: 'back',
  poses: ['Mountain', 'Tree'],
}

function renderPlayer() {
  const onStop = vi.fn()
  const onFinish = vi.fn()
  render(<Player workout={workout} poses={poses} onStop={onStop} onFinish={onFinish} />)
  return { onStop, onFinish }
}

describe('Player: кнопки Завершить и Стоп', () => {
  beforeEach(() => {
    // Финальная фраза играется через new Audio(...).play()
    vi.stubGlobal(
      'Audio',
      class {
        play() {
          return Promise.resolve()
        }
      },
    )
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('Завершить на последней позе завершает тренировку ровно один раз', () => {
    const { onStop, onFinish } = renderPlayer()

    fireEvent.click(screen.getByRole('button', { name: /Пропустить/ }))
    const finishButton = screen.getByRole<HTMLButtonElement>('button', {
      name: /Завершить/,
    })
    fireEvent.click(finishButton)

    // Завершение - это workout_complete (onFinish), а не брошенная тренировка (onStop)
    expect(onFinish).toHaveBeenCalledTimes(1)
    expect(onStop).not.toHaveBeenCalled()

    // Повторное нажатие не должно отправить второй workout_complete
    expect(finishButton.disabled).toBe(true)
    fireEvent.click(finishButton)
    expect(onFinish).toHaveBeenCalledTimes(1)
  })

  it('Стоп передаёт индекс текущей позы', () => {
    const { onStop, onFinish } = renderPlayer()

    fireEvent.click(screen.getByRole('button', { name: /Пропустить/ }))
    fireEvent.click(screen.getByRole('button', { name: '⏹ Стоп' }))
    fireEvent.click(screen.getByRole('button', { name: 'Да, стоп' }))

    // Индекс нужен для workout_abandoned: на какой позе бросили тренировку
    expect(onStop).toHaveBeenCalledWith(1)
    expect(onFinish).not.toHaveBeenCalled()
  })
})
