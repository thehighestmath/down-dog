package io.github.thehighestmath.downdog.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Модели повторяют ответы бэкенда, см. раздел 6 в MVP.md

@Serializable
data class Pose(
    val id: Int,
    @SerialName("name_ru") val nameRu: String,
    @SerialName("name_sanskrit") val nameSanskrit: String? = null,
    @SerialName("name_en") val nameEn: String,
    val category: String? = null,
    val difficulty: String? = null,
    @SerialName("focus_areas") val focusAreas: String? = null,
    val contraindications: String? = null,
    val description: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("audio_url") val audioUrl: String? = null,
    @SerialName("hold_time_sec") val holdTimeSec: Int? = null,
    @SerialName("full_cycle_sec") val fullCycleSec: Int? = null,
) {
    /** Полная ссылка на картинку: бэкенд отдаёт путь вида /api/images/... */
    fun imageUrlFor(baseUrl: String): String? = imageUrl?.let {
        if (it.startsWith("http")) it else baseUrl.trimEnd('/') + it
    }
}

@Serializable
data class Workout(
    val id: String,
    @SerialName("duration_min") val durationMin: Int,
    val level: String,
    val focus: String,
    // name_en поз по порядку, подробности берём из каталога /api/poses
    val poses: List<String>,
)

@Serializable
data class GenerateWorkoutRequest(
    @SerialName("duration_min") val durationMin: Int,
    val level: String,
    val focus: String,
)
