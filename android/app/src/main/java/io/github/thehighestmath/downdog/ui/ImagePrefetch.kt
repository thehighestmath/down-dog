package io.github.thehighestmath.downdog.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.platform.LocalContext
import coil3.SingletonImageLoader
import coil3.request.ImageRequest

/**
 * Заранее скачивает картинки в кеш Coil (память + диск), чтобы во время
 * тренировки поза показывалась сразу, без пустой плашки, и даже без сети.
 * AsyncImage потом берёт картинку из кеша по тому же URL.
 */
@Composable
fun PrefetchImages(urls: List<String>) {
    val context = LocalContext.current
    LaunchedEffect(urls) {
        val imageLoader = SingletonImageLoader.get(context)
        urls.distinct().forEach { url ->
            imageLoader.enqueue(ImageRequest.Builder(context).data(url).build())
        }
    }
}
