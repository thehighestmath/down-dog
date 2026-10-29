package io.github.thehighestmath.downdog.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.github.thehighestmath.downdog.data.Workout

@Composable
fun FinishedScreen(
    workout: Workout,
    onBackToWorkout: () -> Unit,
    onRepeat: () -> Unit,
    onHome: () -> Unit,
    modifier: Modifier = Modifier,
) {
    BackHandler(onBack = onHome)

    Column(
        modifier = modifier.padding(32.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("🎉", fontSize = 64.sp)
        Text(
            "Тренировка завершена!",
            style = MaterialTheme.typography.headlineMedium,
            textAlign = TextAlign.Center,
        )
        Text(
            "${workout.durationMin} мин · ${Level.labelOf(workout.level)} · ${Focus.labelOf(workout.focus)}",
            textAlign = TextAlign.Center,
        )
        Text(
            "Поз в практике: ${workout.poses.size}",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Button(
            onClick = onRepeat,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 24.dp),
        ) { Text("Повторить") }
        OutlinedButton(onClick = onHome, modifier = Modifier.fillMaxWidth()) {
            Text("На главную")
        }
        TextButton(onClick = onBackToWorkout) {
            Text("← Вернуться к последней позе")
        }
    }
}
