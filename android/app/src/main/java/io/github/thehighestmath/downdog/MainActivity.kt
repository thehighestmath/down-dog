package io.github.thehighestmath.downdog

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import io.github.thehighestmath.downdog.ui.DownDogApp
import io.github.thehighestmath.downdog.ui.theme.DownDogTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            DownDogTheme {
                DownDogApp()
            }
        }
    }
}
