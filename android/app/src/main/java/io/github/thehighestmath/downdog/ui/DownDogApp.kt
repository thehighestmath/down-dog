package io.github.thehighestmath.downdog.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

/** Корневой экран: настройки → тренировка → финиш, как в веб-версии. */
@Composable
fun DownDogApp(viewModel: WorkoutViewModel = viewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
        val modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
        val playlist = state.playlist
        val workout = state.workout

        when {
            state.screen == Screen.PLAYER && playlist != null -> PlayerScreen(
                playlist = playlist,
                elapsedSec = state.elapsedSec,
                running = state.running,
                onTogglePause = viewModel::togglePause,
                onPrevious = viewModel::previous,
                onSkip = viewModel::skip,
                onStop = viewModel::stop,
                modifier = modifier,
            )

            state.screen == Screen.FINISHED && workout != null -> FinishedScreen(
                workout = workout,
                onBackToWorkout = viewModel::backToWorkout,
                onRepeat = viewModel::start,
                onHome = viewModel::goHome,
                modifier = modifier,
            )

            else -> HomeScreen(
                state = state,
                onDurationChange = viewModel::setDuration,
                onLevelChange = viewModel::setLevel,
                onFocusChange = viewModel::setFocus,
                onGenerate = viewModel::generate,
                onStart = viewModel::start,
                modifier = modifier,
            )
        }
    }
}
