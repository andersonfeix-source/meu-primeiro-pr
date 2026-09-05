package com.avisamae.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build

/**
 * Ponto único que dispara o alerta em tela cheia, seja a partir de uma
 * mensagem/ligação do WhatsApp (NotificationService) ou de uma ligação
 * comum (CallReceiver).
 *
 * Usamos duas estratégias juntas para máxima confiabilidade entre
 * fabricantes de Android:
 *  1) Notificação de prioridade máxima com setFullScreenIntent — é o
 *     mecanismo oficial do Android para telas cheias tipo "chamada
 *     recebida" / alarme, funciona até com o aparelho bloqueado.
 *  2) Tentativa direta de abrir a Activity, que costuma funcionar porque
 *     serviços de notificação e receivers de estado de chamada têm
 *     permissão do sistema para iniciar uma tela em primeiro plano.
 */
object AlertLauncher {

    enum class Source { WHATSAPP, LIGACAO }

    private const val CHANNEL_ID = "avisa_mae_alerta"
    private const val NOTIFICATION_ID = 4821

    fun launch(context: Context, sender: String, phone: String, message: String, isCall: Boolean, source: Source) {
        val appContext = context.applicationContext
        ensureChannel(appContext)

        val fullScreenIntent = Intent(appContext, AlertActivity::class.java).apply {
            addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_CLEAR_TOP or
                    Intent.FLAG_ACTIVITY_SINGLE_TOP
            )
            putExtra(AlertActivity.EXTRA_SENDER, sender)
            putExtra(AlertActivity.EXTRA_PHONE, phone)
            putExtra(AlertActivity.EXTRA_MESSAGE, message)
            putExtra(AlertActivity.EXTRA_IS_CALL, isCall)
            putExtra(AlertActivity.EXTRA_SOURCE, source.name)
        }

        val pendingIntent = PendingIntent.getActivity(
            appContext,
            NOTIFICATION_ID,
            fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = Notification.Builder(appContext, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_email)
            .setContentTitle(sender)
            .setContentText(message)
            .setCategory(Notification.CATEGORY_CALL)
            .setPriority(Notification.PRIORITY_MAX)
            .setFullScreenIntent(pendingIntent, true)
            .setAutoCancel(true)
            .build()

        val nm = appContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.notify(NOTIFICATION_ID, notification)

        try {
            appContext.startActivity(fullScreenIntent)
        } catch (_: Exception) {
            // Se o sistema bloquear o start direto, a notificação de tela cheia acima
            // ainda garante que o alerta apareça.
        }
    }

    private fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (nm.getNotificationChannel(CHANNEL_ID) != null) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Alertas em tela cheia",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Avisos de mensagens e ligações importantes"
            enableVibration(true)
            setBypassDnd(true)
        }
        nm.createNotificationChannel(channel)
    }
}
