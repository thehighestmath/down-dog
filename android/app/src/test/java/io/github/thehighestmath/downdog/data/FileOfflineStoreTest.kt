package io.github.thehighestmath.downdog.data

import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class FileOfflineStoreTest {

    @get:Rule
    val tmp = TemporaryFolder()

    private fun workout(id: String) = Workout(id, 15, "beginner", "full_body", listOf("A"))

    @Test
    fun `data survives a new store instance`() = runTest {
        val catalog = listOf(Pose(id = 1, nameRu = "Поза А", nameEn = "A"))
        FileOfflineStore(tmp.root).apply {
            saveCatalog(catalog)
            saveWorkout(workout("1"))
        }

        val reopened = FileOfflineStore(tmp.root)
        assertEquals(catalog, reopened.catalog())
        assertEquals(listOf(workout("1")), reopened.workouts())
    }

    @Test
    fun `newest workouts first, without duplicates, limited`() = runTest {
        val store = FileOfflineStore(tmp.root)
        repeat(FileOfflineStore.MAX_WORKOUTS + 5) { store.saveWorkout(workout("$it")) }
        store.saveWorkout(workout("3"))

        val ids = store.workouts().map { it.id }
        assertEquals(FileOfflineStore.MAX_WORKOUTS, ids.size)
        assertEquals("3", ids.first())
        assertEquals(ids.distinct(), ids)
    }

    @Test
    fun `broken file is treated as empty`() = runTest {
        File(tmp.root, "offline.json").writeText("{not json")

        assertTrue(FileOfflineStore(tmp.root).workouts().isEmpty())
    }
}
