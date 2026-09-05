package com.avisamae.app

import android.content.Context

/**
 * Guarda a configuração feita na tela inicial: o(s) nome(s) que devem
 * disparar o alerta (exatamente como aparecem no WhatsApp) e o número
 * de telefone usado para "ligar de volta".
 */
object Prefs {
    private const val FILE = "avisa_mae_prefs"
    private const val KEY_NAMES = "filter_names"
    private const val KEY_PHONE = "callback_phone"

    fun save(context: Context, names: String, phone: String) {
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit()
            .putString(KEY_NAMES, names)
            .putString(KEY_PHONE, phone)
            .apply()
    }

    fun getNames(context: Context): List<String> =
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .getString(KEY_NAMES, "")
            .orEmpty()
            .split(",")
            .map { it.trim() }
            .filter { it.isNotEmpty() }

    fun getRawNames(context: Context): String =
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(KEY_NAMES, "").orEmpty()

    fun getPhone(context: Context): String =
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(KEY_PHONE, "").orEmpty()
}
