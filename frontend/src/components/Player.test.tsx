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
const prefetchPoses = [
  makePose(1, 'Mountain', '/img/mountain.png'),
  makePose(2, 'Tree', '/img/tree.png'),
  makePose(3, 'Warrior', '/img/warrior.png'),
  makePose(4, 'Chair', '/img/chair.png'),
]
const prefetchWorkout: Workout = {
  id: 'w-2',
  duration_min: 2,
  level: 'beginner',
  focus: 'back',
  poses: ['Mountain', 'Tree', 'Warrior', 'Chair'],
}

describe('Player: предзагрузка следующей позы', () => {
  const images: string[] = []
  const sounds: string[] = []
  const playSpy = vi.fn(() => Promise.resolve())

  // Элемент плейлиста для позы с номером idx: из него Player берёт URL ресурсов
  const item = (idx: number) =>
    ({
      name: prefetchWorkout.poses[idx],
      pose: prefetchPoses[idx],
      duration: 30,
    }) as PlaylistItem
  const expectedImage = (idx: number) => poseImageUrl(item(idx))
  const expectedSounds = (idx: number) => poseIntroUrls(item(idx), false, AudioLang.Ru)

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
        decode() {
          return Promise.resolve()
        }
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

  it('через 500 мс запрашивает картинку и озвучку позы N+1 и не играет звук', () => {
    renderPlayer(prefetchWorkout, prefetchPoses)
    expect(expectedSounds(1).length).toBeGreaterThan(0)

    // Сразу после старта предзагрузка ещё не началась: сначала озвучка текущей позы
    expect(images).toEqual([])
    expect(sounds).toEqual([])

    wait(PREFETCH_DELAY_MS)

    expect(images).toEqual([expectedImage(1)])
    expect(sounds).toEqual(expectedSounds(1))
    expect(playSpy).not.toHaveBeenCalled()
  })

  it('на последней позе ничего лишнего не грузится', () => {
    renderPlayer(prefetchWorkout, prefetchPoses)

    // Доходим до последней позы, давая отработать предзагрузке каждой
    for (let i = 0; i < 3; i++) {
      skip()
      wait(PREFETCH_DELAY_MS)
    }
    expect(images).toContain(expectedImage(3))

    images.length = 0
    sounds.length = 0
    wait(PREFETCH_DELAY_MS * 4)

    expect(images).toEqual([])
    expect(sounds).toEqual([])
  })

  it('после «Пропустить» подгружается поза, следующая за новой', () => {
    renderPlayer(prefetchWorkout, prefetchPoses)

    skip() // теперь поза 2 (индекс 1), следующая - индекс 2
    wait(PREFETCH_DELAY_MS)

    expect(images).toEqual([expectedImage(2)])
    expect(sounds).toEqual(expectedSounds(2))
  })

  it('быстрая серия «Пропустить» грузит только итоговую позу', () => {
    renderPlayer(prefetchWorkout, prefetchPoses)

    // Два нажатия быстрее задержки предзагрузки: позы 1 и 2 пользователь не видел
    skip()
    skip()
    wait(PREFETCH_DELAY_MS)

    expect(images).toEqual([expectedImage(3)])
    expect(sounds).toEqual(expectedSounds(3))
  })
})
