package io.github.thehighestmath.downdog.ui

// Варианты настроек тренировки. apiValue — то, что принимает бэкенд.

enum class Level(val apiValue: String, val label: String) {
    BEGINNER("beginner", "Новичок"),
    INTERMEDIATE("intermediate", "Средний"),
    ADVANCED("advanced", "Продвинутый"),
    ;

    companion object {
        fun labelOf(apiValue: String) = entries.find { it.apiValue == apiValue }?.label ?: apiValue
    }
}

enum class Focus(val apiValue: String, val label: String) {
    BACK("back", "Спина"),
    NECK("neck", "Шея"),
    LEGS("legs", "Ноги"),
    FULL_BODY("full_body", "Всё тело"),
    RELAXATION("relaxation", "Расслабление"),
    ;

    companion object {
        fun labelOf(apiValue: String) = entries.find { it.apiValue == apiValue }?.label ?: apiValue
    }
}

val DURATIONS_MIN = listOf(5, 10, 15, 20, 30)
