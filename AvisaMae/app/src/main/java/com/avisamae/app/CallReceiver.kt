package com.avisamae.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager

/**
 * Detecta uma ligação comum (não WhatsApp) tocando no aparelho e, se o
 * número bater com o configurado nas preferências, dispara o mesmo
 * alerta em tela cheia usado para o WhatsApp.
 *
 * Ler o número que está ligando (EXTRA_INCOMING_NUMBER) exige as
 * permissões READ_PHONE_STATE e READ_CALL_LOG concedidas pelo usuário.
 */
class CallReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != TelephonyManager.ACTION_PHONE_STATE_CHANGED) return
        val state = intent.getStringExtra(TelephonyManager.EXTRA_STATE)
        if (state != TelephonyManager.EXTRA_STATE_RINGING) return

        val configuredPhone = Prefs.getPhone(context)
        if (configuredPhone.isBlank()) return

        val incomingNumber = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER).orEmpty()
        if (!numbersMatch(incomingNumber, configuredPhone)) return

        AlertLauncher.launch(
            context = context.applicationContext,
            sender = Prefs.getNames(context).firstOrNull() ?: "Ligação",
            message = "Chamada recebida",
            isCall = true,
            source = AlertLauncher.Source.LIGACAO
        )
    }

    private fun numbersMatch(a: String, b: String): Boolean {
        val da = a.filter { it.isDigit() }.takeLast(8)
        val db = b.filter { it.isDigit() }.takeLast(8)
        return da.isNotEmpty() && da == db
    }
}
