package io.github.thehighestmath.downdog.data

import io.github.thehighestmath.downdog.BuildConfig
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import okhttp3.MediaType.Companion.toMediaType
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import java.io.IOException

interface DownDogApi {
    @GET("api/poses")
    suspend fun getPoses(): List<Pose>

    @POST("api/workouts/generate")
    suspend fun generateWorkout(@Body request: GenerateWorkoutRequest): Workout

    @GET("api/workouts/{id}")
    suspend fun getWorkout(@Path("id") id: String): Workout

    companion object {
        private val json = Json { ignoreUnknownKeys = true }

        fun create(baseUrl: String = BuildConfig.API_BASE_URL): DownDogApi =
            Retrofit.Builder()
                .baseUrl(baseUrl)
                .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
                .build()
                .create(DownDogApi::class.java)

        /** Текст ошибки для пользователя. Для 400 бэкенд кладёт причину в `detail`. */
        fun errorMessage(e: Throwable): String = when (e) {
            is HttpException -> detailOf(e) ?: "Ошибка сервера (${e.code()})"
            is IOException -> "Нет связи с сервером. Проверьте, что бэкенд запущен."
            else -> e.message ?: "Неизвестная ошибка"
        }

        private fun detailOf(e: HttpException): String? {
            val body = e.response()?.errorBody()?.string() ?: return null
            val detail = runCatching { json.parseToJsonElement(body) as? JsonObject }
                .getOrNull()?.get("detail")
            return (detail as? JsonPrimitive)?.content
        }
    }
}
