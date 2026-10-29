package io.github.thehighestmath.downdog.ui

import io.github.thehighestmath.downdog.data.DownDogApi
import io.github.thehighestmath.downdog.data.GenerateWorkoutRequest
import io.github.thehighestmath.downdog.data.Pose
import io.github.thehighestmath.downdog.data.Workout
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
class WorkoutViewModelTest {

    private val dispatcher = StandardTestDispatcher()

    private class FakeApi(
        private val poses: List<Pose> = listOf(
            Pose(id = 1, nameRu = "Поза А", nameEn = "A", fullCycleSec = 10),
            Pose(id = 2, nameRu = "Поза Б", nameEn = "B", fullCycleSec = 10),
        ),
        private val workoutPoses: List<String> = listOf("A", "B"),
        private val failPoses: Boolean = false,
    ) : DownDogApi {
        var lastRequest: GenerateWorkoutRequest? = null

        override suspend fun getPoses(): List<Pose> =
            if (failPoses) throw IOException("offline") else poses

        override suspend fun generateWorkout(request: GenerateWorkoutRequest): Workout {
            lastRequest = request
            return Workout("id-1", request.durationMin, request.level, request.focus, workoutPoses)
        }

        override suspend fun getWorkout(id: String): Workout = error("not used")
    }

    @Before
    fun setUp() = Dispatchers.setMain(dispatcher)

    @After
    fun tearDown() = Dispatchers.resetMain()

    private fun TestScope.readyViewModel(api: FakeApi = FakeApi()): WorkoutViewModel {
        val vm = WorkoutViewModel(api)
        vm.generate()
        runCurrent()
        return vm
    }

    @Test
    fun `generate sends selected settings`() = runTest(dispatcher) {
        val api = FakeApi()
        val vm = WorkoutViewModel(api)
        vm.setDuration(20)
        vm.setLevel(Level.ADVANCED)
        vm.setFocus(Focus.LEGS)
        vm.generate()
        runCurrent()

        assertEquals(GenerateWorkoutRequest(20, "advanced", "legs"), api.lastRequest)
        assertNotNull(vm.state.value.workout)
        assertFalse(vm.state.value.loading)
    }

    @Test
    fun `changing settings drops generated workout`() = runTest(dispatcher) {
        val vm = readyViewModel()
        vm.setFocus(Focus.BACK)

        assertNull(vm.state.value.workout)
    }

    @Test
    fun `catalog failure shows error`() = runTest(dispatcher) {
        val vm = WorkoutViewModel(FakeApi(failPoses = true))
        runCurrent()

        assertTrue(vm.state.value.error!!.startsWith("Не удалось загрузить позы"))
    }

    @Test
    fun `timer ticks, pauses and finishes the workout`() = runTest(dispatcher) {
        val vm = readyViewModel()
        vm.start()
        assertEquals(Screen.PLAYER, vm.state.value.screen)

        advanceTimeBy(3_001)
        assertEquals(3, vm.state.value.elapsedSec)

        vm.togglePause()
        advanceTimeBy(5_000)
        assertEquals(3, vm.state.value.elapsedSec)

        vm.togglePause()
        advanceTimeBy(17_001)
        assertEquals(Screen.FINISHED, vm.state.value.screen)
        assertFalse(vm.state.value.running)
    }

    @Test
    fun `skip on last pose finishes the workout`() = runTest(dispatcher) {
        val vm = readyViewModel()
        vm.start()

        vm.skip()
        assertEquals(10, vm.state.value.elapsedSec)
        vm.skip()
        assertEquals(Screen.FINISHED, vm.state.value.screen)
    }

    @Test
    fun `previous after accidental skip returns to the skipped pose`() = runTest(dispatcher) {
        val vm = readyViewModel()
        vm.start()
        advanceTimeBy(4_001)

        vm.skip()
        vm.previous()

        assertEquals(0, vm.state.value.elapsedSec)
    }

    @Test
    fun `back to workout from finish resumes the last pose`() = runTest(dispatcher) {
        val vm = readyViewModel()
        vm.start()
        vm.skip()
        vm.skip()
        assertEquals(Screen.FINISHED, vm.state.value.screen)

        vm.backToWorkout()

        assertEquals(Screen.PLAYER, vm.state.value.screen)
        assertEquals(10, vm.state.value.elapsedSec)
        assertTrue(vm.state.value.running)
    }

    @Test
    fun `stop returns home and stops the timer`() = runTest(dispatcher) {
        val vm = readyViewModel()
        vm.start()
        vm.stop()
        advanceTimeBy(5_000)

        assertEquals(Screen.HOME, vm.state.value.screen)
        assertNull(vm.state.value.playlist)
        assertFalse(vm.state.value.running)
    }

    @Test
    fun `empty workout cannot be started`() = runTest(dispatcher) {
        val vm = readyViewModel(FakeApi(workoutPoses = emptyList()))
        vm.start()

        assertEquals(Screen.HOME, vm.state.value.screen)
    }
}
