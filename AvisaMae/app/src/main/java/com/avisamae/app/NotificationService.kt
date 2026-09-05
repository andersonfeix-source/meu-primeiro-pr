package com.avisamae.app

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

/**
 * Fica "ouvindo" as notificações do sistema. Quando o WhatsApp posta uma
 * notificação de mensagem ou ligação de um contato configurado nas
 * preferências, dispara o alerta em tela cheia.
 *
 * Precisa que a mãe conceda "Acesso a notificações" para este app em
 * Ajustes > Apps > Acesso especial > Acesso a notificações.
 */
class NotificationService : NotificationListenerService() {

    private val whatsappPackages = setOf("com.whatsapp", "com.whatsapp.w4b")

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        super.onNotificationPosted(sbn)
        if (sbn.packageName !in whatsappPackages) return

        val extras = sbn.notification.extras
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        if (title.isBlank()) return

        val filterNames = Prefs.getNames(applicationContext)
        if (filterNames.isEmpty()) return
        val matches = filterNames.any { title.trim().equals(it.trim(), ignoreCase = true) }
        if (!matches) return

        val isCall = sbn.notification.category == Notification.CATEGORY_CALL ||
            text.contains("chamada de voz", ignoreCase = true) ||
            text.contains("chamada de vídeo", ignoreCase = true) ||
            text.contains("videochamada", ignoreCase = true)

        AlertLauncher.launch(
            context = applicationContext,
            sender = title,
            message = text.ifBlank { "Nova mensagem no WhatsApp" },
            isCall = isCall,
            source = AlertLauncher.Source.WHATSAPP
        )
    }
}
