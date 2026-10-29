package io.github.thehighestmath.downdog.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil3.compose.AsyncImage
import io.github.thehighestmath.downdog.BuildConfig
import io.github.thehighestmath.downdog.workout.Playlist

@Composable
fun PlayerScreen(
    playlist: Playlist,
    elapsedSec: Int,
    running: Boolean,
    onTogglePause: () -> Unit,
    onPrevious: () -> Unit,
    onSkip: () -> Unit,
    onStop: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var confirmStop by rememberSaveable { mutableStateOf(false) }
    BackHandler { confirmStop = true }
    KeepScreenOn()

    val position = playlist.positionAt(elapsedSec)
    val item = playlist.items[position.index]
    val next = playlist.items.getOrNull(position.index + 1)

    Column(modifier = modifier.padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                "Поза ${position.index + 1} из ${playlist.items.size}",
                style = MaterialTheme.typography.labelLarge,
                modifier = Modifier.weight(1f),
            )
            TextButton(onClick = { confirmStop = true }) { Text("Стоп") }
        }
        LinearProgressIndicator(
            progress = { elapsedSec.toFloat() / playlist.totalSec },
            modifier = Modifier.fillMaxWidth(),
        )

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            PoseImage(
                url = item.pose?.imageUrlFor(BuildConfig.API_BASE_URL),
                contentDescription = item.pose?.nameRu ?: item.name,
            )
            // Название и таймер в одну строку, чтобы описание помещалось на экран
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        item.pose?.nameRu ?: item.name,
                        style = MaterialTheme.typography.headlineSmall,
                    )
                    item.pose?.nameSanskrit?.let {
                        Text(
                            "$it · ${item.name}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                Text(
                    formatTime(position.timeLeftSec),
                    style = MaterialTheme.typography.displaySmall,
                    fontWeight = FontWeight.Bold,
                    color = if (position.timeLeftSec <= 3) {
                        MaterialTheme.colorScheme.error
                    } else {
                        MaterialTheme.colorScheme.onSurface
                    },
                    modifier = Modifier.padding(start = 12.dp),
                )
            }
            item.pose?.description?.let {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Text(it, modifier = Modifier.padding(16.dp))
                }
            }
            next?.let {
                Text(
                    "Далее: ${it.pose?.nameRu ?: it.name}",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        val buttonPadding = PaddingValues(horizontal = 8.dp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(
                onClick = onPrevious,
                contentPadding = buttonPadding,
                modifier = Modifier.weight(1f),
            ) { Text("← Назад") }
            Button(
                onClick = onTogglePause,
                contentPadding = buttonPadding,
                modifier = Modifier.weight(1f),
            ) { Text(if (running) "Пауза" else "Продолжить") }
            OutlinedButton(
                onClick = onSkip,
                contentPadding = buttonPadding,
                modifier = Modifier.weight(1f),
            ) { Text(if (next == null) "Завершить" else "Далее →") }
        }
    }

    if (confirmStop) {
        AlertDialog(
            onDismissRequest = { confirmStop = false },
            title = { Text("Завершить тренировку досрочно?") },
            confirmButton = {
                TextButton(onClick = {
                    confirmStop = false
                    onStop()
                }) { Text("Да, стоп") }
            },
            dismissButton = {
                TextButton(onClick = { confirmStop = false }) { Text("Отмена") }
            },
        )
    }
}

/**
 * Картинка позы. Если картинки нет или она не загрузилась — заглушка того же
 * размера, чтобы экран не прыгал от позы к позе.
 */
@Composable
private fun PoseImage(url: String?, contentDescription: String) {
    var failed by remember(url) { mutableStateOf(false) }
    val showImage = url != null && !failed

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxWidth()
            .height(200.dp)
            .clip(RoundedCornerShape(16.dp))
            // Картинки нарисованы на белом фоне, поэтому подложка белая и в тёмной теме
            .background(if (showImage) Color.White else MaterialTheme.colorScheme.surfaceVariant),
    ) {
        if (showImage) {
            AsyncImage(
                model = url,
                contentDescription = contentDescription,
                contentScale = ContentScale.Fit,
                onError = { failed = true },
                modifier = Modifier.fillMaxSize(),
            )
        } else {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("🧘", fontSize = 56.sp)
                Text(
                    "Картинка скоро появится",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

/** Пока идёт тренировка, экран не гаснет. */
@Composable
private fun KeepScreenOn() {
    val view = LocalView.current
    DisposableEffect(view) {
        view.keepScreenOn = true
        onDispose { view.keepScreenOn = false }
    }
}

private fun formatTime(totalSec: Int): String {
    val minutes = (totalSec / 60).toString().padStart(2, '0')
    val seconds = (totalSec % 60).toString().padStart(2, '0')
    return "$minutes:$seconds"
}
