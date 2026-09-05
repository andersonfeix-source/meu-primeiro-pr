package com.avisamae.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager

/**
 * Detecta uma ligação comum (não WhatsApp) tocando no aparelho e, se o
 * número bater com alguma pessoa configurada nas preferências, dispara o
 * mesmo alerta em tela cheia usado para o WhatsApp.
 *
 * Ler o número que está ligando (EXTRA_INCOMING_NUMBER) exige as
 * permissões READ_PHONE_STATE e READ_CALL_LOG concedidas pelo usuário.
 */
class CallReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != TelephonyManager.ACTION_PHONE_STATE_CHANGED) return
        val state = intent.getStringExtra(TelephonyManager.EXTRA_STATE)
        if (state != TelephonyManager.EXTRA_STATE_RINGING) return

        val incomingNumber = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER).orEmpty()
        val contato = Prefs.findByPhone(context, incomingNumber) ?: return

        AlertLauncher.launch(
            context = context.applicationContext,
            sender = contato.name.ifBlank { "Ligação" },
            phone = contato.phone,
            message = "Chamada recebida",
            isCall = true,
            source = AlertLauncher.Source.LIGACAO
        )
    }
}
