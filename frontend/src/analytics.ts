const API_URL = 'http://localhost:8000/api'


function getUserId(): string {
  const key = 'analytics_user_id'
  let userId = localStorage.getItem(key)

  if (!userId) {
    userId = crypto.randomUUID()
    localStorage.setItem(key, userId)
  }

  return userId
}


const sessionId: string = crypto.randomUUID()


type AnalyticsEventType =
  'workout_started' | 'workout_completed' | 'workout_abandoned' | 'pose_viewed'


export async function trackEvent(
  eventType: AnalyticsEventType,
  payload: Record<string, unknown> = {},
): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/analytics/track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        user_id: getUserId(),
        session_id: sessionId,
        payload: payload,
      }),
    })

    if (!response.ok) {
      console.warn(
        `[analytics] Ошибка трекинга (${response.status}):`,
        await response.text(),
      )
    }
  } catch (err) {
    console.warn('[analytics] Не удалось отправить событие:', err)
  }
}


export function trackWorkoutStarted(
  workoutId: string,
  params: { duration_min: number; level: string; focus: string },
) {
  return trackEvent('workout_started', {
    workout_id: workoutId,
    ...params,
  })
}

export function trackWorkoutCompleted(
  workoutId: string,
  params?: { poses_count?: number },
) {
  return trackEvent('workout_completed', {
    workout_id: workoutId,
    ...params,
  })
}

export function trackWorkoutAbandoned(
  workoutId: string,
  params?: { current_pose_index?: number; reason?: string },
) {
  return trackEvent('workout_abandoned', {
    workout_id: workoutId,
    ...params,
  })
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
