package com.avisamae.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

data class Contato(val name: String, val phone: String)

/**
 * Guarda a lista de pessoas configuradas na tela inicial: cada uma com o
 * nome exatamente como aparece no WhatsApp e o telefone correspondente,
 * usados para detectar mensagens/ligações e para os botões de resposta.
 */
object Prefs {
    private const val FILE = "avisa_mae_prefs"
    private const val KEY_CONTACTS = "contacts_json"

    fun saveContacts(context: Context, contacts: List<Contato>) {
        val array = JSONArray()
        contacts.forEach { contato ->
            array.put(
                JSONObject().apply {
                    put("name", contato.name)
                    put("phone", contato.phone)
                }
            )
        }
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit()
            .putString(KEY_CONTACTS, array.toString())
            .apply()
    }

    fun getContacts(context: Context): List<Contato> {
        val raw = context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .getString(KEY_CONTACTS, null) ?: return emptyList()
        return try {
            val array = JSONArray(raw)
            (0 until array.length()).mapNotNull { i ->
                val obj = array.optJSONObject(i) ?: return@mapNotNull null
                val name = obj.optString("name").trim()
                val phone = obj.optString("phone").trim()
                if (name.isBlank() && phone.isBlank()) null else Contato(name, phone)
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun findByName(context: Context, title: String): Contato? =
        getContacts(context).firstOrNull {
            it.name.isNotBlank() && title.trim().equals(it.name, ignoreCase = true)
        }

    fun findByPhone(context: Context, incomingNumber: String): Contato? =
        getContacts(context).firstOrNull {
            it.phone.isNotBlank() && numbersMatch(incomingNumber, it.phone)
        }

    private fun numbersMatch(a: String, b: String): Boolean {
        val da = a.filter { it.isDigit() }.takeLast(8)
        val db = b.filter { it.isDigit() }.takeLast(8)
        return da.isNotEmpty() && da == db
    }
}
