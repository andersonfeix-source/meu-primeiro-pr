package com.avisamae.app

import android.content.Context

/**
 * Guarda a configuração feita na tela inicial: o(s) nome(s) que devem
 * disparar o alerta (exatamente como aparecem no WhatsApp) e o(s)
 * telefone(s) usados para detectar ligações e para "ligar de volta".
 */
object Prefs {
    private const val FILE = "avisa_mae_prefs"
    private const val KEY_NAMES = "filter_names"
    private const val KEY_PHONES = "callback_phones"

    fun save(context: Context, names: String, phones: String) {
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit()
            .putString(KEY_NAMES, names)
            .putString(KEY_PHONES, phones)
            .apply()
    }

    fun getNames(context: Context): List<String> =
        splitList(context, KEY_NAMES)

    fun getRawNames(context: Context): String =
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(KEY_NAMES, "").orEmpty()

    fun getPhones(context: Context): List<String> =
        splitList(context, KEY_PHONES)

    fun getRawPhones(context: Context): String =
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(KEY_PHONES, "").orEmpty()

    /** Primeiro número configurado, usado pelos botões "Ligar de volta" e "Abrir WhatsApp". */
    fun getPhone(context: Context): String =
        getPhones(context).firstOrNull().orEmpty()

    private fun splitList(context: Context, key: String): List<String> =
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .getString(key, "")
            .orEmpty()
            .split(",")
            .map { it.trim() }
            .filter { it.isNotEmpty() }
}
