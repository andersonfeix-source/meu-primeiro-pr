package com.avisamae.app

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.avisamae.app.databinding.ActivityMainBinding

/**
 * Tela de configuração: quem vai disparar o alerta (nome exatamente como
 * aparece no WhatsApp da mãe) e o telefone para "ligar de volta", além
 * dos atalhos para conceder as permissões especiais necessárias.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    private val runtimePermissions: Array<String> by lazy {
        mutableListOf(
            android.Manifest.permission.READ_PHONE_STATE,
            android.Manifest.permission.READ_CALL_LOG,
            android.Manifest.permission.CALL_PHONE
        ).apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                add(android.Manifest.permission.ANSWER_PHONE_CALLS)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                add(android.Manifest.permission.POST_NOTIFICATIONS)
            }
        }.toTypedArray()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.inputNames.setText(Prefs.getRawNames(this))
        binding.inputPhone.setText(Prefs.getPhone(this))

        binding.buttonSave.setOnClickListener {
            Prefs.save(this, binding.inputNames.text.toString(), binding.inputPhone.text.toString())
            Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show()
        }

        binding.buttonNotificationAccess.setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }

        binding.buttonBattery.setOnClickListener { requestIgnoreBatteryOptimizations() }

        binding.buttonPermissions.setOnClickListener {
            ActivityCompat.requestPermissions(this, runtimePermissions, 1001)
        }

        binding.buttonFullScreenSettings.setOnClickListener { openFullScreenIntentSettings() }

        binding.buttonTest.setOnClickListener {
            val firstName = Prefs.getNames(this).firstOrNull().takeUnless { it.isNullOrBlank() }
                ?: getString(R.string.test_sender_fallback)
            AlertLauncher.launch(
                this,
                sender = firstName,
                message = getString(R.string.test_message),
                isCall = false,
                source = AlertLauncher.Source.WHATSAPP
            )
        }
    }

    override fun onResume() {
        super.onResume()
        updateStatus()
    }

    private fun updateStatus() {
        binding.textStatusNotifications.text = if (isNotificationListenerEnabled()) {
            getString(R.string.status_notifications_on)
        } else {
            getString(R.string.status_notifications_off)
        }
    }

    private fun isNotificationListenerEnabled(): Boolean {
        val flat = Settings.Secure.getString(contentResolver, "enabled_notification_listeners")
        return flat?.contains(packageName) == true
    }

    private fun requestIgnoreBatteryOptimizations() {
        val pm = getSystemService(POWER_SERVICE) as PowerManager
        if (!pm.isIgnoringBatteryOptimizations(packageName)) {
            startActivity(
                Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                    data = Uri.parse("package:$packageName")
                }
            )
        } else {
            Toast.makeText(this, R.string.battery_already_ok, Toast.LENGTH_SHORT).show()
        }
    }

    private fun openFullScreenIntentSettings() {
        if (Build.VERSION.SDK_INT >= 34) {
            try {
                startActivity(
                    Intent("android.settings.MANAGE_APP_USE_FULL_SCREEN_INTENT").apply {
                        data = Uri.parse("package:$packageName")
                    }
                )
            } catch (_: Exception) {
                Toast.makeText(this, R.string.full_screen_settings_unavailable, Toast.LENGTH_SHORT).show()
            }
        } else {
            Toast.makeText(this, R.string.full_screen_settings_not_needed, Toast.LENGTH_SHORT).show()
        }
    }
}
