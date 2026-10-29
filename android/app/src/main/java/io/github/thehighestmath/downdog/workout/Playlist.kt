package io.github.thehighestmath.downdog.workout

import io.github.thehighestmath.downdog.data.Pose

/** Поза в тренировке. [pose] = null, если её нет в каталоге. */
data class PlaylistItem(
    val name: String,
    val pose: Pose?,
    val durationSec: Int,
)

/** Где мы в тренировке: номер позы и сколько секунд ей осталось. */
data class Position(
    val index: Int,
    val timeLeftSec: Int,
)

/**
 * Тренировка как последовательность поз с длительностями.
 * Логика та же, что в веб-плеере (frontend/src/components/Player.tsx).
 */
class Playlist(val items: List<PlaylistItem>) {
    init {
        require(items.isNotEmpty()) { "Пустая тренировка" }
    }

    // Смещения начала каждой позы и конец тренировки: [0, 30, 65, ..., totalSec]
    private val offsets: List<Int> = items.runningFold(0) { acc, item -> acc + item.durationSec }

    val totalSec: Int = offsets.last()

    fun positionAt(elapsedSec: Int): Position {
        for (i in items.indices) {
            if (elapsedSec < offsets[i + 1]) {
                return Position(i, offsets[i + 1] - elapsedSec)
            }
        }
        return Position(items.lastIndex, 0)
    }

    /** Секунда, с которой начинается поза [index]. */
    fun startOf(index: Int): Int = offsets[index]

    /** Секунда, с которой начинается поза после [index]; для последней — конец тренировки. */
    fun startOfNext(index: Int): Int = offsets[(index + 1).coerceAtMost(items.size)]

    /**
     * Куда перейти по кнопке «Назад», как в музыкальных плеерах: в первые
     * [RESTART_GRACE_SEC] секунды позы — на предыдущую (например, если случайно
     * нажали «Пропустить»), позже — в начало текущей.
     */
    fun startOfPrevious(elapsedSec: Int): Int {
        val index = positionAt(elapsedSec).index
        val inPoseSec = elapsedSec - offsets[index]
        return if (inPoseSec < RESTART_GRACE_SEC && index > 0) offsets[index - 1] else offsets[index]
    }

    companion object {
        const val MIN_POSE_SEC = 5
        const val DEFAULT_POSE_SEC = 30
        const val RESTART_GRACE_SEC = 3

        fun build(poseNames: List<String>, catalog: Map<String, Pose>): Playlist =
            Playlist(
                poseNames.map { name ->
                    val pose = catalog[name]
                    PlaylistItem(
                        name = name,
                        pose = pose,
                        durationSec = maxOf(MIN_POSE_SEC, pose?.fullCycleSec ?: DEFAULT_POSE_SEC),
                    )
                },
            )
    }
}
