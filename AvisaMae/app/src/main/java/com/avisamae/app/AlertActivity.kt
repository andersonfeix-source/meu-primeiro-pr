package com.avisamae.app

import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.media.Ringtone
import android.media.RingtoneManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.telecom.TelecomManager
import android.view.View
import android.view.WindowManager
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import com.avisamae.app.databinding.ActivityAlertBinding

/**
 * Tela cheia que cobre qualquer outro app (inclusive a tela de bloqueio)
 * para avisar que chegou uma mensagem ou ligação importante. Só fecha
 * pelos botões desta tela — o botão "voltar" do Android é ignorado de
 * propósito, para garantir que o aviso seja realmente visto.
 */
class AlertActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_SENDER = "extra_sender"
        const val EXTRA_PHONE = "extra_phone"
        const val EXTRA_MESSAGE = "extra_message"
        const val EXTRA_IS_CALL = "extra_is_call"
        const val EXTRA_SOURCE = "extra_source"
    }

    private lateinit var binding: ActivityAlertBinding
    private var ringtone: Ringtone? = null
    private var vibrator: Vibrator? = null
    private var phone: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        applyLockScreenFlags()

        binding = ActivityAlertBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val sender = intent.getStringExtra(EXTRA_SENDER).orEmpty()
        phone = intent.getStringExtra(EXTRA_PHONE).orEmpty()
        val message = intent.getStringExtra(EXTRA_MESSAGE).orEmpty()
        val isCall = intent.getBooleanExtra(EXTRA_IS_CALL, false)
        val source = intent.getStringExtra(EXTRA_SOURCE)

        binding.textHeadline.text = if (isCall) getString(R.string.alert_headline_call, sender)
        else getString(R.string.alert_headline_message, sender)
        binding.textMessage.text = message.ifBlank { getString(R.string.alert_default_message) }

        binding.buttonOpenWhatsapp.visibility =
            if (source == AlertLauncher.Source.WHATSAPP.name) View.VISIBLE else View.GONE

        binding.buttonAnswerCall.visibility =
            if (isCall && source == AlertLauncher.Source.LIGACAO.name) View.VISIBLE else View.GONE

        binding.buttonOpenWhatsapp.setOnClickListener {
            openWhatsapp()
            dismiss()
        }
        binding.buttonCallBack.setOnClickListener {
            callBack()
            dismiss()
        }
        binding.buttonAnswerCall.setOnClickListener {
            answerCall()
            dismiss()
        }
        binding.buttonClose.setOnClickListener { dismiss() }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                // Intencionalmente vazio: só os botões da tela fecham o aviso.
            }
        })

        startAlerting()
    }

    private fun applyLockScreenFlags() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
            )
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
    }

    private fun startAlerting() {
        try {
            val uri = RingtoneManager.getActualDefaultRingtoneUri(this, RingtoneManager.TYPE_NOTIFICATION)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            ringtone = RingtoneManager.getRingtone(this, uri)?.apply {
                audioAttributes = AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
                isLooping = true
                play()
            }
        } catch (_: Exception) {
            // Sem som disponível não é motivo para travar o alerta.
        }

        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (getSystemService(VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(VIBRATOR_SERVICE) as Vibrator
        }
        val pattern = longArrayOf(0, 800, 400, 800, 400, 800)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator?.vibrate(VibrationEffect.createWaveform(pattern, 0))
        } else {
            @Suppress("DEPRECATION")
            vibrator?.vibrate(pattern, 0)
        }
    }

    private fun stopAlerting() {
        try {
            ringtone?.stop()
        } catch (_: Exception) { }
        vibrator?.cancel()
    }

    private fun openWhatsapp() {
        if (phone.isNotBlank()) {
            val digits = phone.filter { it.isDigit() }.removePrefix("0")
            val international = if (digits.startsWith("55")) digits else "55$digits"
            for (pkg in listOf("com.whatsapp", "com.whatsapp.w4b")) {
                try {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://wa.me/$international")).apply {
                        setPackage(pkg)
                    }
                    startActivity(intent)
                    return
                } catch (_: Exception) { }
            }
        }

        val launchIntent = packageManager.getLaunchIntentForPackage("com.whatsapp")
            ?: packageManager.getLaunchIntentForPackage("com.whatsapp.w4b")
        launchIntent?.let { startActivity(it) }
    }

    private fun callBack() {
        if (phone.isBlank()) return
        val uri = Uri.parse("tel:$phone")
        val hasCallPermission = checkSelfPermission(android.Manifest.permission.CALL_PHONE) ==
            PackageManager.PERMISSION_GRANTED
        val action = if (hasCallPermission) Intent.ACTION_CALL else Intent.ACTION_DIAL
        startActivity(Intent(action, uri))
    }

    private fun answerCall() {
        try {
            if (checkSelfPermission(android.Manifest.permission.ANSWER_PHONE_CALLS) ==
                PackageManager.PERMISSION_GRANTED
            ) {
                val telecomManager = getSystemService(TELECOM_SERVICE) as TelecomManager
                telecomManager.acceptRingingCall()
            }
        } catch (_: Exception) { }
    }

    private fun dismiss() {
        stopAlerting()
        finish()
    }

    override fun onDestroy() {
        stopAlerting()
        super.onDestroy()
    }
}
