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
import com.avisamae.app.databinding.ItemContactBinding

/**
 * Tela de configuração: quem vai disparar o alerta (nome exatamente como
 * aparece no WhatsApp da mãe, e o telefone de cada pessoa), além dos
 * atalhos para conceder as permissões especiais necessárias.
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

        val existing = Prefs.getContacts(this)
        if (existing.isEmpty()) {
            addContactRow()
        } else {
            existing.forEach { addContactRow(it.name, it.phone) }
        }

        binding.buttonAddContact.setOnClickListener { addContactRow() }

        binding.buttonSave.setOnClickListener {
            Prefs.saveContacts(this, collectContacts())
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
            val contato = collectContacts().firstOrNull()
            AlertLauncher.launch(
                this,
                sender = contato?.name?.takeUnless { it.isBlank() } ?: getString(R.string.test_sender_fallback),
                phone = contato?.phone.orEmpty(),
                message = getString(R.string.test_message),
                isCall = false,
                source = AlertLauncher.Source.WHATSAPP
            )
        }
    }

    private fun addContactRow(name: String = "", phone: String = "") {
        val row = ItemContactBinding.inflate(layoutInflater, binding.contactsContainer, false)
        row.inputContactName.setText(name)
        row.inputContactPhone.setText(phone)
        row.buttonRemove.setOnClickListener {
            binding.contactsContainer.removeView(row.root)
        }
        binding.contactsContainer.addView(row.root)
    }

    private fun collectContacts(): List<Contato> =
        (0 until binding.contactsContainer.childCount).mapNotNull { i ->
            val row = ItemContactBinding.bind(binding.contactsContainer.getChildAt(i))
            val name = row.inputContactName.text.toString().trim()
            val phone = row.inputContactPhone.text.toString().trim()
            if (name.isBlank() && phone.isBlank()) null else Contato(name, phone)
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
