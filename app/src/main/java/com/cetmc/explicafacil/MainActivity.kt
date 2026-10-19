package com.cetmc.explicafacil

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cetmc.explicafacil.ui.theme.ExplicaFacilTheme
import org.json.JSONArray
import org.json.JSONObject
import java.util.Calendar
import java.util.Locale
import java.util.UUID

// Cada marcação reúne os dados escolhidos no formulário.
data class Marcacao(val id: String, val disciplina: String, val professor: String, val instante: Long)

private val professores = linkedMapOf(
    "Matemática" to listOf("Ana Silva", "João Costa"),
    "Português" to listOf("Maria Santos", "Pedro Gomes"),
    "Inglês" to listOf("Sofia Martins", "Rui Ferreira")
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ExplicaFacilTheme { ExplicaFacil() } }
    }
}

// Guardamos os dados no telemóvel para não desaparecerem ao fechar a aplicação.
private fun carregar(context: Context): List<Marcacao> = try {
    val dados = JSONArray(context.getSharedPreferences("explica_facil", Context.MODE_PRIVATE)
        .getString("marcacoes", "[]"))
    (0 until dados.length()).map { i ->
        val item = dados.getJSONObject(i)
        Marcacao(item.getString("id"), item.getString("disciplina"),
            item.getString("professor"), item.getLong("instante"))
    }.sortedBy { it.instante }
} catch (_: org.json.JSONException) { emptyList() }

private fun guardar(context: Context, marcacoes: List<Marcacao>) {
    val dados = JSONArray()
    marcacoes.forEach {
        dados.put(JSONObject().put("id", it.id).put("disciplina", it.disciplina)
            .put("professor", it.professor).put("instante", it.instante))
    }
    context.getSharedPreferences("explica_facil", Context.MODE_PRIVATE).edit()
        .putString("marcacoes", dados.toString()).apply()
}

@Composable
private fun Escolha(titulo: String, atual: String, opcoes: List<String>, escolher: (String) -> Unit) {
    var aberto by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth()) {
        OutlinedButton(onClick = { aberto = true }, modifier = Modifier.fillMaxWidth()) {
            Text("$titulo: $atual")
        }
        DropdownMenu(expanded = aberto, onDismissRequest = { aberto = false }) {
            opcoes.forEach { opcao ->
                DropdownMenuItem(text = { Text(opcao) }, onClick = { escolher(opcao); aberto = false })
            }
        }
    }
}

@Composable
fun ExplicaFacil() {
    val context = LocalContext.current
    var marcacoes by remember { mutableStateOf(carregar(context)) }
    var disciplina by remember { mutableStateOf("Matemática") }
    var professor by remember { mutableStateOf(professores.getValue(disciplina).first()) }
    var dia by remember { mutableStateOf<Long?>(null) }
    var hora by remember { mutableStateOf<Int?>(null) }
    var minuto by remember { mutableStateOf(0) }
    var mensagem by remember { mutableStateOf("") }
    var erro by remember { mutableStateOf(false) }
    var cancelar by remember { mutableStateOf<Marcacao?>(null) }
    val formatoDia = remember { java.text.SimpleDateFormat("dd/MM/yyyy", Locale("pt", "PT")) }
    val formatoCompleto = remember { java.text.SimpleDateFormat("dd/MM/yyyy 'às' HH:mm", Locale("pt", "PT")) }

    Scaffold { margem ->
        Column(Modifier.fillMaxSize().padding(margem).verticalScroll(rememberScrollState())
            .padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Explica Fácil", style = MaterialTheme.typography.headlineLarge,
                color = MaterialTheme.colorScheme.primary)
            Text("Uma ajuda para aprender melhor.")
            HorizontalDivider()
            Text("Marcar explicação", style = MaterialTheme.typography.titleLarge)
            Escolha("Disciplina", disciplina, professores.keys.toList()) {
                disciplina = it
                professor = professores.getValue(it).first()
                mensagem = ""
            }
            Escolha("Professor", professor, professores.getValue(disciplina)) { professor = it; mensagem = "" }
            OutlinedButton(modifier = Modifier.fillMaxWidth(), onClick = {
                val calendario = Calendar.getInstance()
                dia?.let { calendario.timeInMillis = it }
                val seletor = DatePickerDialog(context, { _, ano, mes, data ->
                    dia = Calendar.getInstance().apply {
                        set(ano, mes, data, 0, 0, 0); set(Calendar.MILLISECOND, 0)
                    }.timeInMillis
                    mensagem = ""
                }, calendario.get(Calendar.YEAR), calendario.get(Calendar.MONTH), calendario.get(Calendar.DAY_OF_MONTH))
                seletor.datePicker.minDate = System.currentTimeMillis()
                seletor.show()
            }) { Text(dia?.let { "Dia: ${formatoDia.format(java.util.Date(it))}" } ?: "Escolher dia") }
            OutlinedButton(modifier = Modifier.fillMaxWidth(), onClick = {
                TimePickerDialog(context, { _, h, m -> hora = h; minuto = m; mensagem = "" },
                    hora ?: 15, minuto, true).show()
            }) { Text(hora?.let { String.format(Locale.ROOT, "Hora: %02d:%02d", it, minuto) } ?: "Escolher hora") }
            Button(modifier = Modifier.fillMaxWidth(), onClick = {
                val data = dia
                val h = hora
                erro = true
                if (data == null || h == null) {
                    mensagem = "Escolhe o dia e a hora."
                } else {
                    val instante = Calendar.getInstance().apply {
                        timeInMillis = data; set(Calendar.HOUR_OF_DAY, h); set(Calendar.MINUTE, minuto)
                    }.timeInMillis
                    when {
                        instante <= System.currentTimeMillis() -> mensagem = "Escolhe uma data e hora futuras."
                        marcacoes.any { it.instante == instante } -> mensagem = "Já tens uma explicação marcada para esta hora."
                        else -> {
                            marcacoes = (marcacoes + Marcacao(UUID.randomUUID().toString(), disciplina, professor, instante)).sortedBy { it.instante }
                            guardar(context, marcacoes)
                            erro = false
                            mensagem = "Explicação marcada com sucesso!"
                            dia = null; hora = null; minuto = 0
                        }
                    }
                }
            }) { Text("Marcar explicação") }
            if (mensagem.isNotEmpty()) Text(mensagem,
                color = if (erro) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
            HorizontalDivider()
            Text("As minhas marcações", style = MaterialTheme.typography.titleLarge)
            if (marcacoes.isEmpty()) Text("Ainda não tens explicações marcadas.")
            marcacoes.forEach { marcacao ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(marcacao.disciplina, style = MaterialTheme.typography.titleMedium)
                        Text("Professor: ${marcacao.professor}")
                        Text(formatoCompleto.format(java.util.Date(marcacao.instante)))
                        TextButton(onClick = { cancelar = marcacao }) { Text("Cancelar marcação") }
                    }
                }
            }
        }
    }
    cancelar?.let { marcacao ->
        AlertDialog(onDismissRequest = { cancelar = null }, title = { Text("Cancelar explicação?") },
            text = { Text("${marcacao.disciplina} — ${formatoCompleto.format(java.util.Date(marcacao.instante))}") },
            confirmButton = { TextButton(onClick = {
                marcacoes = marcacoes.filterNot { it.id == marcacao.id }
                guardar(context, marcacoes)
                cancelar = null; mensagem = "Marcação cancelada."; erro = false
            }) { Text("Sim, cancelar") } },
            dismissButton = { TextButton(onClick = { cancelar = null }) { Text("Manter marcação") } })
    }
}
