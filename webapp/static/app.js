const ABREVIACAO_DIA = {
  SEGUNDA: "SEG",
  TERCA: "TER",
  QUARTA: "QUA",
  QUINTA: "QUI",
  SEXTA: "SEX",
  SABADO: "SAB",
};

const PALETA_DISCIPLINAS = [
  "#ffd6d6", "#ffe8c2", "#fff7c2", "#dcf5c2",
  "#c2f0e0", "#c2e4ff", "#dcd0ff", "#ffd0ec",
];

const form = document.getElementById("form-parametros");
const status = document.getElementById("status");
const resultado = document.getElementById("resultado");
const tabelaRelatorioBody = document.querySelector("#tabela-relatorio tbody");
const seletorTurma = document.getElementById("seletor-turma");
const gradeContainer = document.getElementById("grade-container");

let ultimoResultado = null;

function corDaDisciplina(nome) {
  let hash = 0;
  for (let i = 0; i < nome.length; i++) {
    hash = (hash * 31 + nome.charCodeAt(i)) % PALETA_DISCIPLINAS.length;
  }
  return PALETA_DISCIPLINAS[hash];
}

function preencherValor(nomeCampo, valor) {
  if (valor === undefined) return;
  if (Array.isArray(valor)) {
    for (const input of form.querySelectorAll(`[name="${nomeCampo}"]`)) {
      input.checked = valor.includes(input.value);
    }
    return;
  }
  const input = form.elements[nomeCampo];
  if (input) {
    input.value = valor;
  }
}

async function carregarParametrosPadrao() {
  const resposta = await fetch("/api/parametros-padrao");
  const defaults = await resposta.json();
  for (const [campo, valor] of Object.entries(defaults.instancia)) {
    preencherValor(`instancia.${campo}`, valor);
  }
  for (const [campo, valor] of Object.entries(defaults.ag)) {
    preencherValor(`ag.${campo}`, valor);
  }
}

function coletarParametros() {
  const dados = { instancia: {}, ag: {} };
  for (const input of form.elements) {
    if (!input.name || !input.name.includes(".")) continue;
    const [grupo, campo] = input.name.split(".");

    if (input.type === "checkbox") {
      if (!(campo in dados[grupo])) dados[grupo][campo] = [];
      if (input.checked) dados[grupo][campo].push(input.value);
      continue;
    }

    dados[grupo][campo] = input.dataset.tipo === "float"
      ? parseFloat(input.value)
      : parseInt(input.value, 10);
  }
  return dados;
}

function renderizarRelatorio(relatorio, piso) {
  const linhas = [
    ["Fitness (valor final)", relatorio.valor, null],
    ["Conflitos de professor", relatorio.violacoes_professor, piso.minimo_conflitos_professor],
    ["Conflitos de sala", relatorio.violacoes_sala, piso.minimo_conflitos_sala],
    ["Conflitos de turma", relatorio.violacoes_turma, piso.minimo_conflitos_turma],
    ["Minutos excedentes de carga horária", relatorio.minutos_excedentes_carga_horaria, piso.minimo_minutos_excedentes_carga_horaria],
    ["Violações de disponibilidade", relatorio.violacoes_disponibilidade, piso.minimo_violacoes_disponibilidade],
  ];

  tabelaRelatorioBody.innerHTML = "";
  for (const [rotulo, encontrado, pisoValor] of linhas) {
    const tr = document.createElement("tr");
    const bateu = pisoValor === null ? "" : (encontrado === pisoValor ? "sim" : "não");
    tr.innerHTML = `<td>${rotulo}</td><td>${encontrado}</td><td>${pisoValor ?? "—"}</td><td>${bateu}</td>`;
    tabelaRelatorioBody.appendChild(tr);
  }
}

function renderizarGrade(turmaId) {
  const { dias, numeros_aula, slots, grade_por_turma, turmas } = ultimoResultado;
  const turma = turmas.find((t) => t.id === turmaId);

  // slots de outros turnos podem repetir (dia, numero_aula) -- restringe ao turno da turma
  // antes de montar o lookup, senao as celulas colidem (ver motor_horarios/visualizacao.py).
  const slotsDoTurno = slots.filter((s) => s.turno === turma.turno);
  const slotIdPorPosicao = {};
  for (const slot of slotsDoTurno) {
    slotIdPorPosicao[`${slot.dia_semana}-${slot.numero_aula}`] = slot.id;
  }
  const gradeTurma = grade_por_turma[turmaId] || {};

  const tabela = document.createElement("table");
  const thead = document.createElement("thead");
  thead.innerHTML = `<tr><th>Aula</th>${dias.map((d) => `<th>${ABREVIACAO_DIA[d] || d}</th>`).join("")}</tr>`;
  tabela.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const numero of numeros_aula) {
    const tr = document.createElement("tr");
    let linha = `<td>${numero}</td>`;
    for (const dia of dias) {
      const slotId = slotIdPorPosicao[`${dia}-${numero}`];
      const info = slotId !== undefined ? gradeTurma[slotId] : undefined;
      if (info) {
        linha += `<td style="background:${corDaDisciplina(info.disciplina)}">${info.disciplina}<br><small>${info.professor} · ${info.sala}</small></td>`;
      } else {
        linha += "<td></td>";
      }
    }
    tr.innerHTML = linha;
    tbody.appendChild(tr);
  }
  tabela.appendChild(tbody);

  gradeContainer.innerHTML = "";
  gradeContainer.appendChild(tabela);
}

function renderizarResultado(dados) {
  ultimoResultado = dados;
  renderizarRelatorio(dados.relatorio, dados.piso_teorico);

  seletorTurma.innerHTML = dados.turmas
    .map((turma) => `<option value="${turma.id}">${turma.nome}</option>`)
    .join("");
  renderizarGrade(dados.turmas[0]?.id);

  resultado.hidden = false;
}

seletorTurma.addEventListener("change", () => {
  renderizarGrade(parseInt(seletorTurma.value, 10));
});

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const botao = form.querySelector("button[type=submit]");
  botao.disabled = true;
  status.textContent = "Executando o algoritmo genético... pode levar alguns segundos.";
  resultado.hidden = true;

  try {
    const resposta = await fetch("/api/executar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletarParametros()),
    });
    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.erro || `Erro ${resposta.status}`);
    }
    status.textContent = "";
    renderizarResultado(dados);
  } catch (erro) {
    status.textContent = `Erro: ${erro.message}`;
  } finally {
    botao.disabled = false;
  }
});

carregarParametrosPadrao().catch((erro) => {
  status.textContent = `Erro ao carregar parâmetros padrão: ${erro.message}`;
});
