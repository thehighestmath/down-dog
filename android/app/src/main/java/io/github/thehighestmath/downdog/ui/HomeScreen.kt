package io.github.thehighestmath.downdog.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import io.github.thehighestmath.downdog.data.Pose
import io.github.thehighestmath.downdog.data.Workout

@Composable
fun HomeScreen(
    state: UiState,
    onDurationChange: (Int) -> Unit,
    onLevelChange: (Level) -> Unit,
    onFocusChange: (Focus) -> Unit,
    onGenerate: () -> Unit,
    onStart: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column {
            Text("Йога-тренировка", style = MaterialTheme.typography.headlineMedium)
            Text(
                "Поз в каталоге: ${state.catalog.size}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        state.error?.let { ErrorCard(it) }

        OptionGroup("Длительность", DURATIONS_MIN, state.durationMin, { "$it мин" }, onDurationChange)
        OptionGroup("Уровень", Level.entries, state.level, { it.label }, onLevelChange)
        OptionGroup("Фокус", Focus.entries, state.focus, { it.label }, onFocusChange)

        Button(
            onClick = onGenerate,
            enabled = !state.loading,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (state.loading) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
            } else {
                Text("Подобрать тренировку")
            }
        }

        state.workout?.let { WorkoutPreview(it, state.catalog, onStart) }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun <T> OptionGroup(
    title: String,
    options: List<T>,
    selected: T,
    label: (T) -> String,
    onSelect: (T) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, style = MaterialTheme.typography.titleMedium)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { option ->
                FilterChip(
                    selected = option == selected,
                    onClick = { onSelect(option) },
                    label = { Text(label(option)) },
                )
            }
        }
    }
}

@Composable
private fun ErrorCard(message: String) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.errorContainer,
            contentColor = MaterialTheme.colorScheme.onErrorContainer,
        ),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(message, modifier = Modifier.padding(16.dp))
    }
}

@Composable
private fun WorkoutPreview(workout: Workout, catalog: Map<String, Pose>, onStart: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Тренировка готова", style = MaterialTheme.typography.titleLarge)
            Text(
                "${workout.durationMin} мин · ${Level.labelOf(workout.level)} · " +
                    "${Focus.labelOf(workout.focus)} · поз: ${workout.poses.size}",
                style = MaterialTheme.typography.bodyMedium,
            )
            if (workout.poses.isEmpty()) {
                Text("Под эти настройки не нашлось поз. Попробуйте другой фокус или уровень.")
            } else {
                workout.poses.forEachIndexed { i, name ->
                    Text("${i + 1}. ${catalog[name]?.nameRu ?: name}")
                }
                Button(onClick = onStart, modifier = Modifier.fillMaxWidth()) {
                    Text("Начать")
                }
            }
        }
    }
}
