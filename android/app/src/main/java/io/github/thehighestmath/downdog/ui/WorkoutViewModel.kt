package io.github.thehighestmath.downdog.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import io.github.thehighestmath.downdog.data.DownDogApi
import io.github.thehighestmath.downdog.data.GenerateWorkoutRequest
import io.github.thehighestmath.downdog.data.OfflineStore
import io.github.thehighestmath.downdog.data.Pose
import io.github.thehighestmath.downdog.data.Workout
import io.github.thehighestmath.downdog.workout.Playlist
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.IOException

enum class Screen { HOME, PLAYER, FINISHED }

data class UiState(
    val screen: Screen = Screen.HOME,
    // Каталог поз по name_en: генератор возвращает именно его
    val catalog: Map<String, Pose> = emptyMap(),
    val durationMin: Int = 15,
    val level: Level = Level.BEGINNER,
    val focus: Focus = Focus.FULL_BODY,
    val loading: Boolean = false,
    val error: String? = null,
    // Не ошибка, а пояснение: например, что работаем без связи с сервером
    val notice: String? = null,
    val workout: Workout? = null,
    val playlist: Playlist? = null,
    val elapsedSec: Int = 0,
    val running: Boolean = false,
)

class WorkoutViewModel(
    private val api: DownDogApi = DownDogApi.create(),
    private val store: OfflineStore,
) : ViewModel() {

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    private var timer: Job? = null

    init {
        viewModelScope.launch { loadCatalog() }
    }

    // --- Настройки ---
    // Поменяли настройки — старая тренировка им уже не соответствует.

    fun setDuration(minutes: Int) =
        _state.update { it.copy(durationMin = minutes, workout = null, notice = null) }

    fun setLevel(level: Level) = _state.update { it.copy(level = level, workout = null, notice = null) }

    fun setFocus(focus: Focus) = _state.update { it.copy(focus = focus, workout = null, notice = null) }

    fun generate() {
        val s = _state.value
        if (s.loading) return
        _state.update { it.copy(loading = true, error = null, notice = null, workout = null) }
        viewModelScope.launch {
            // Если бэкенд не отвечал на старте, пробуем загрузить каталог ещё раз
            if (_state.value.catalog.isEmpty()) loadCatalog()
            try {
                val workout = api.generateWorkout(
                    GenerateWorkoutRequest(s.durationMin, s.level.apiValue, s.focus.apiValue),
                )
                _state.update { it.copy(workout = workout) }
                store.saveWorkout(workout)
            } catch (e: CancellationException) {
                throw e
            } catch (e: IOException) {
                // Нет связи — достаём из памяти тренировку с такими же настройками
                val saved = store.workouts().firstOrNull {
                    it.durationMin == s.durationMin &&
                        it.level == s.level.apiValue &&
                        it.focus == s.focus.apiValue
                }
                _state.update {
                    if (saved != null) {
                        it.copy(workout = saved, notice = "Нет связи с сервером — показываем сохранённую тренировку.")
                    } else {
                        it.copy(
                            error = DownDogApi.errorMessage(e) +
                                " Сохранённых тренировок с такими настройками нет.",
                        )
                    }
                }
            } catch (e: Exception) {
                _state.update { it.copy(error = DownDogApi.errorMessage(e)) }
            } finally {
                _state.update { it.copy(loading = false) }
            }
        }
    }

    // --- Тренировка ---

    fun start() {
        val s = _state.value
        val workout = s.workout ?: return
        if (workout.poses.isEmpty()) return
        _state.update {
            it.copy(
                screen = Screen.PLAYER,
                playlist = Playlist.build(workout.poses, s.catalog),
                elapsedSec = 0,
            )
        }
        resume()
    }

    fun togglePause() = if (_state.value.running) pause() else resume()

    fun skip() {
        val s = _state.value
        val playlist = s.playlist ?: return
        seekTo(playlist.startOfNext(playlist.positionAt(s.elapsedSec).index))
    }

    fun previous() {
        val s = _state.value
        val playlist = s.playlist ?: return
        seekTo(playlist.startOfPrevious(s.elapsedSec))
    }

    /** С экрана завершения обратно к последней позе, если «Завершить» нажали случайно. */
    fun backToWorkout() {
        val playlist = _state.value.playlist ?: return
        _state.update {
            it.copy(screen = Screen.PLAYER, elapsedSec = playlist.startOf(playlist.items.lastIndex))
        }
        resume()
    }

    fun stop() {
        timer?.cancel()
        _state.update { it.copy(screen = Screen.HOME, playlist = null, running = false) }
    }

    fun goHome() = _state.update { it.copy(screen = Screen.HOME, playlist = null) }

    private fun resume() {
        timer?.cancel()
        _state.update { it.copy(running = true) }
        timer = viewModelScope.launch {
            while (true) {
                delay(1000)
                seekTo(_state.value.elapsedSec + 1)
            }
        }
    }

    private fun pause() {
        timer?.cancel()
        _state.update { it.copy(running = false) }
    }

    private fun seekTo(sec: Int) {
        val playlist = _state.value.playlist ?: return
        if (sec >= playlist.totalSec) {
            timer?.cancel()
            _state.update {
                it.copy(screen = Screen.FINISHED, elapsedSec = playlist.totalSec, running = false)
            }
        } else {
            _state.update { it.copy(elapsedSec = sec) }
        }
    }

    private suspend fun loadCatalog() {
        try {
            val poses = api.getPoses()
            setCatalog(poses)
            store.saveCatalog(poses)
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            val saved = store.catalog()
            if (saved.isNotEmpty()) {
                setCatalog(saved)
            } else {
                _state.update { it.copy(error = "Не удалось загрузить позы. ${DownDogApi.errorMessage(e)}") }
            }
        }
    }

    private fun setCatalog(poses: List<Pose>) =
        _state.update { it.copy(catalog = poses.associateBy { pose -> pose.nameEn }) }
}
