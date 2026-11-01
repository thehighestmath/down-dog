package io.github.thehighestmath.downdog.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File

/** Копия каталога и сгенерированных тренировок на телефоне — на случай, когда нет связи. */
interface OfflineStore {
    suspend fun catalog(): List<Pose>

    suspend fun saveCatalog(poses: List<Pose>)

    /** Сохранённые тренировки, самые свежие первыми. */
    suspend fun workouts(): List<Workout>

    suspend fun saveWorkout(workout: Workout)
}

@Serializable
private data class OfflineData(
    val catalog: List<Pose> = emptyList(),
    val workouts: List<Workout> = emptyList(),
)

/** Хранит всё в одном JSON-файле во внутренней памяти приложения. */
class FileOfflineStore(dir: File) : OfflineStore {
    private val file = File(dir, "offline.json")
    private val json = Json { ignoreUnknownKeys = true }
    private val mutex = Mutex()

    override suspend fun catalog() = read().catalog

    override suspend fun saveCatalog(poses: List<Pose>) = update { it.copy(catalog = poses) }

    override suspend fun workouts() = read().workouts

    override suspend fun saveWorkout(workout: Workout) = update { data ->
        val workouts = listOf(workout) + data.workouts.filter { it.id != workout.id }
        data.copy(workouts = workouts.take(MAX_WORKOUTS))
    }

    private suspend fun read(): OfflineData = mutex.withLock { readUnlocked() }

    private suspend fun update(change: (OfflineData) -> OfflineData) = mutex.withLock {
        val text = json.encodeToString(change(readUnlocked()))
        withContext(Dispatchers.IO) {
            // Пишем во временный файл и подменяем: если приложение убьют посреди записи,
            // старые данные останутся целыми. Не записалось (например, кончилось место) —
            // не страшно, это только запасная копия.
            runCatching {
                val tmp = File(file.path + ".tmp")
                tmp.writeText(text)
                tmp.renameTo(file)
            }
        }
        Unit
    }

    private suspend fun readUnlocked(): OfflineData = withContext(Dispatchers.IO) {
        if (!file.exists()) return@withContext OfflineData()
        // Битый или старый формат файла — просто начинаем с чистого листа
        runCatching { json.decodeFromString<OfflineData>(file.readText()) }.getOrDefault(OfflineData())
    }

    companion object {
        const val MAX_WORKOUTS = 30
    }
}
