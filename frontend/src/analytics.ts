const API_URL = '/api'

function getUserId(): string {
  const key = 'analytics_user_id'
  let userId = localStorage.getItem(key)

  if (!userId) {
    userId = crypto.randomUUID()
    localStorage.setItem(key, userId)
  }

  return userId
}

let currentSessionId: string | null = null

export function startAnalyticsSession(): string {
  currentSessionId = crypto.randomUUID()
  return currentSessionId
}

export function getSessionId(): string {
  if (!currentSessionId) {
    currentSessionId = crypto.randomUUID()
  }
  return currentSessionId
}

export function endAnalyticsSession(): void {
  currentSessionId = null
}

export type AnalyticsEventType =
  'workout_started' | 'workout_completed' | 'workout_abandoned' | 'pose_viewed'

async function sendEventWithRetry(body: string, maxRetries = 2): Promise<boolean> {
  const endpoint = `${API_URL}/analytics/track`
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        keepalive: true,
      })

      if (response.ok) {
        return true
      }

      console.warn(
        `[analytics] Ошибка трекинга (${response.status}):`,
        await response.text(),
      )
      // Клиентские 4xx ошибки ретраить бессмысленно
      if (response.status >= 400 && response.status < 500) {
        return false
      }
    } catch (err) {
      if (attempt === maxRetries) {
        console.warn('[analytics] Не удалось отправить событие после повторов:', err)
        return false
      }
      await new Promise((resolve) => setTimeout(resolve, 500 * (attempt + 1)))
    }
  }
  return false
}

export async function trackEvent(
  eventType: AnalyticsEventType,
  payload: Record<string, unknown> = {},
): Promise<void> {
  const body = JSON.stringify({
    event_type: eventType,
    user_id: getUserId(),
    session_id: getSessionId(),
    payload: payload,
  })

  await sendEventWithRetry(body)
}

export function trackWorkoutStarted(
  workoutId: string,
  params: { duration_min: number; level: string; focus: string },
) {
  // Для каждой новой тренировки генерируется отдельный session_id
  startAnalyticsSession()
  return trackEvent('workout_started', {
    workout_id: workoutId,
    ...params,
  })
}

export async function trackWorkoutCompleted(
  workoutId: string,
  params?: { poses_count?: number },
) {
  try {
    await trackEvent('workout_completed', {
      workout_id: workoutId,
      ...params,
    })
  } finally {
    endAnalyticsSession()
  }
}

export async function trackWorkoutAbandoned(
  workoutId: string,
  params?: { current_pose_index?: number; reason?: string },
) {
  try {
    await trackEvent('workout_abandoned', {
      workout_id: workoutId,
      ...params,
    })
  } finally {
    endAnalyticsSession()
  }
}

export function trackPoseViewed(
  workoutId: string,
  poseName: string,
  poseIndex: number,
) {
  return trackEvent('pose_viewed', {
    workout_id: workoutId,
    pose_name: poseName,
    pose_index: poseIndex,
  })
}
