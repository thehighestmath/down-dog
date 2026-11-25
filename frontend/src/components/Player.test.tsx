import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AudioLang, poseIntroUrls } from '../audio'
import type { PlaylistItem, Pose, Workout } from '../types'
import { PREFETCH_DELAY_MS, poseImageUrl } from '../utils/Prefetch'
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

function makePose(id: number, nameEn: string, imageUrl: string | null = null): Pose {
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
    image_url: imageUrl,
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

function renderPlayer(w: Workout = workout, p: Pose[] = poses) {
  const onStop = vi.fn()
  const onFinish = vi.fn()
  render(<Player workout={w} poses={p} onStop={onStop} onFinish={onFinish} />)
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

// NF-02: пока идёт поза N, в фоне грузятся картинка и озвучка позы N+1
const names = ['Mountain', 'Tree', 'Warrior', 'Chair']
const prefetchPoses = names.map((n, i) => makePose(i + 1, n, `/img/${n}.png`))
const prefetchWorkout: Workout = { ...workout, poses: names }

describe('Player: предзагрузка следующей позы', () => {
  const images: string[] = []
  const sounds: string[] = []
  const playSpy = vi.fn(() => Promise.resolve())

  // Ресурсы, которые Player должен запросить для позы с номером idx
  const resourcesOf = (idx: number) => {
    const item = {
      name: names[idx],
      pose: prefetchPoses[idx],
      duration: 30,
    } as PlaylistItem
    return {
      images: [poseImageUrl(item)],
      sounds: poseIntroUrls(item, false, AudioLang.Ru),
    }
  }
  const skip = () => fireEvent.click(screen.getByRole('button', { name: /Пропустить/ }))
  const wait = (ms: number) =>
    act(() => {
      vi.advanceTimersByTime(ms)
    })

  beforeEach(() => {
    vi.useFakeTimers()
    images.length = 0
    sounds.length = 0
    playSpy.mockClear()
    // Предзагрузка создаёт Image и Audio, но ничего не показывает и не играет
    vi.stubGlobal(
      'Image',
      class {
        decode = () => Promise.resolve()
        set src(url: string) {
          images.push(url)
        }
      },
    )
    vi.stubGlobal(
      'Audio',
      class {
        preload = ''
        play = playSpy
        load() {}
        set src(url: string) {
          sounds.push(url)
        }
      },
    )
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it.each([
    { name: 'после старта: поза 2', skips: 0, target: 1 },
    { name: 'после «Пропустить»: поза, следующая за новой', skips: 1, target: 2 },
    { name: 'после быстрой серии «Пропустить»: только итоговая', skips: 2, target: 3 },
  ])('через 500 мс грузится $name', ({ skips, target }) => {
    renderPlayer(prefetchWorkout, prefetchPoses)
    expect(resourcesOf(target).sounds.length).toBeGreaterThan(0)
    for (let i = 0; i < skips; i++) skip()

    // До истечения задержки ничего не запрашивается: сначала озвучка текущей позы
    expect({ images, sounds }).toEqual({ images: [], sounds: [] })

    wait(PREFETCH_DELAY_MS)
    expect({ images, sounds }).toEqual(resourcesOf(target))
    expect(playSpy).not.toHaveBeenCalled() // загрузка без воспроизведения
  })

  it('на последней позе ничего лишнего не грузится', () => {
    renderPlayer(prefetchWorkout, prefetchPoses)
    skip()
    skip()
    skip() // индекс 3: последняя поза
    wait(PREFETCH_DELAY_MS * 4)
    expect({ images, sounds }).toEqual({ images: [], sounds: [] })
  })
})
