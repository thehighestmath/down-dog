package io.github.thehighestmath.downdog.workout

import io.github.thehighestmath.downdog.data.Pose
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class PlaylistTest {

    private fun pose(nameEn: String, fullCycleSec: Int?) =
        Pose(id = 0, nameRu = nameEn, nameEn = nameEn, fullCycleSec = fullCycleSec)

    private val catalog = listOf(pose("A", 30), pose("B", 20), pose("Short", 2), pose("NoTime", null))
        .associateBy { it.nameEn }

    @Test
    fun `durations come from catalog with fallback and minimum`() {
        val playlist = Playlist.build(listOf("A", "Short", "NoTime", "Unknown"), catalog)

        assertEquals(
            listOf(30, Playlist.MIN_POSE_SEC, Playlist.DEFAULT_POSE_SEC, Playlist.DEFAULT_POSE_SEC),
            playlist.items.map { it.durationSec },
        )
        assertNull(playlist.items[3].pose)
        assertEquals(30 + 5 + 30 + 30, playlist.totalSec)
    }

    @Test
    fun `position moves to next pose at its start`() {
        val playlist = Playlist.build(listOf("A", "B"), catalog)

        assertEquals(Position(index = 0, timeLeftSec = 30), playlist.positionAt(0))
        assertEquals(Position(index = 0, timeLeftSec = 1), playlist.positionAt(29))
        assertEquals(Position(index = 1, timeLeftSec = 20), playlist.positionAt(30))
        assertEquals(Position(index = 1, timeLeftSec = 0), playlist.positionAt(50))
    }

    @Test
    fun `skip jumps to next pose or to the end`() {
        val playlist = Playlist.build(listOf("A", "B"), catalog)

        assertEquals(30, playlist.startOfNext(0))
        assertEquals(50, playlist.startOfNext(1))
    }

    @Test
    fun `previous goes back a pose right after skip, otherwise restarts current`() {
        val playlist = Playlist.build(listOf("A", "B"), catalog)

        assertEquals(0, playlist.startOfPrevious(30)) // только что перешли на B
        assertEquals(0, playlist.startOfPrevious(32))
        assertEquals(30, playlist.startOfPrevious(33)) // B идёт уже 3 секунды
        assertEquals(0, playlist.startOfPrevious(1)) // первая поза — в её начало
    }

    @Test
    fun `image url is joined with backend address`() {
        val withImage = pose("A", 30).copy(imageUrl = "/api/images/Поза горы.png")

        assertEquals(
            "http://10.0.2.2:8000/api/images/Поза горы.png",
            withImage.imageUrlFor("http://10.0.2.2:8000/"),
        )
        assertNull(pose("B", 30).imageUrlFor("http://10.0.2.2:8000/"))
    }

    @Test(expected = IllegalArgumentException::class)
    fun `empty workout is rejected`() {
        Playlist.build(emptyList(), catalog)
    }
}
