import { listar } from './listagens-api.js';
import './dashboard.css';

const el = id => document.getElementById(id);
const admin = ['Admin', 'Super Admin'].includes(sessionStorage.getItem('estok.perfil'));
const numero = n => n.toLocaleString('pt-BR');
const estados = [['Pendante', 'Pendentes', 'bg-amber-400'], ['Em_Andamento', 'Em andamento', 'bg-indigo-400'], ['Concluida', 'Concluídas', 'bg-emerald-400']];

function texto(tag, conteudo, classe = '') {
  const node = document.createElement(tag); node.textContent = conteudo; node.className = classe; return node;
}

function indicador(titulo, resultado, href, nota) {
  const link = document.createElement('a'); link.href = href;
  link.className = 'rounded-xl border border-white/10 bg-gray-950 p-6 transition hover:border-indigo-400/50';
  link.append(texto('p', titulo, 'text-sm text-gray-400'));
  link.append(texto('p', resultado.status === 'fulfilled' ? numero(resultado.value.length) : '—', 'mt-3 text-3xl font-bold text-white'));
  link.append(texto('p', resultado.status === 'fulfilled' ? nota : 'Não foi possível carregar', 'mt-2 text-sm text-gray-400'));
  return link;
}

function tarefas(resultado) {
  el('dashboard-status').replaceChildren(); el('dashboard-prazos').replaceChildren();
  if (resultado.status !== 'fulfilled') {
    el('dashboard-status').append(texto('p', 'Não foi possível consultar a situação das tarefas.', 'text-sm text-gray-400'));
    el('dashboard-prazos').append(texto('li', 'Prazos indisponíveis. Tente atualizar o painel.', 'text-sm text-gray-400'));
    return;
  }
  const registros = resultado.value;
  for (const [codigo, rotulo, cor] of estados) {
    const quantidade = registros.filter(t => t.status === codigo).length;
    const grupo = document.createElement('div');
    const legenda = document.createElement('div'); legenda.className = 'mb-2 flex justify-between text-sm';
    legenda.append(texto('span', rotulo, 'text-gray-300'), texto('span', numero(quantidade), 'font-semibold'));
    const trilho = document.createElement('div'); trilho.className = 'h-2 overflow-hidden rounded-full bg-gray-800'; trilho.setAttribute('aria-hidden', 'true');
    const barra = document.createElement('div'); barra.className = `h-full rounded-full ${cor}`;
    barra.style.width = `${registros.length ? quantidade / registros.length * 100 : 0}%`;
    trilho.append(barra); grupo.append(legenda, trilho); el('dashboard-status').append(grupo);
  }
  const abertas = registros.filter(t => t.status !== 'Concluida').sort((a, b) => String(a.prazo).localeCompare(String(b.prazo))).slice(0, 5);
  const agora = new Date();
  const hoje = `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, '0')}-${String(agora.getDate()).padStart(2, '0')}`;
  for (const tarefa of abertas) {
    const li = document.createElement('li'); li.className = 'flex flex-wrap items-center justify-between gap-2 py-4';
    const prazo = String(tarefa.prazo || '').slice(0, 10);
    const vencida = /^\d{4}-\d{2}-\d{2}$/.test(prazo) && prazo < hoje;
    li.append(texto('span', tarefa.titulo, 'min-w-0 break-words text-sm font-medium'));
    li.append(texto('span', `${vencida ? 'Atrasada · ' : ''}${prazo ? prazo.split('-').reverse().join('/') : 'Sem prazo'}`, vencida ? 'text-sm text-amber-300' : 'text-sm text-gray-400'));
    el('dashboard-prazos').append(li);
  }
  if (!abertas.length) el('dashboard-prazos').append(texto('li', registros.length ? 'Todas as tarefas estão concluídas.' : 'Nenhuma tarefa cadastrada para este perfil.', 'py-4 text-sm text-gray-400'));
}

async function carregar() {
  const atualizar = el('dashboard-atualizar'); atualizar.disabled = true;
  el('dashboard-aviso').textContent = 'Carregando indicadores…';
  const fontes = [
    ['Itens do patrimônio', '/itens/all', 'inventario.html', 'Itens cadastrados'],
    ['Localizações', '/localizacoes/all', 'localizacoes.html', 'Locais cadastrados'],
    [admin ? 'Tarefas' : 'Minhas tarefas', '/tarefas/all', 'tarefa.html', admin ? 'Conferências cadastradas' : 'Conferências atribuídas a você'],
  ];
  if (admin) fontes.push(['Usuários', '/usuarios/all', 'usuarios.html', 'Contas cadastradas']);
  try {
    const resultados = await Promise.allSettled(fontes.map(([, endpoint]) => listar(endpoint)));
    el('dashboard-indicadores').replaceChildren(...fontes.map(([titulo, , href, nota], i) => indicador(titulo, resultados[i], href, nota)));
    tarefas(resultados[2]);
    const falhas = resultados.flatMap((r, i) => r.status === 'rejected' ? [fontes[i][0]] : []);
    const sessaoExpirada = resultados.some(r => r.status === 'rejected' && r.reason.status === 401);
    el('dashboard-aviso').textContent = sessaoExpirada ? 'Sua sessão não está ativa. Entre novamente para consultar os dados.' :
      falhas.length ? `Não foi possível carregar: ${falhas.join(', ')}.${falhas.length < fontes.length ? ' Os demais indicadores estão disponíveis.' : ' Verifique a conexão com a API e tente novamente.'}` :
        `Atualizado às ${new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}.`;
  } finally { atualizar.disabled = false; }
}

el('dashboard-resumo').textContent = admin ? 'Visão geral do patrimônio e das conferências da equipe.' : 'Acompanhe o patrimônio e as conferências atribuídas a você.';
el('dashboard-usuarios').hidden = !admin;
el('dashboard-atualizar').addEventListener('click', carregar);
carregar();
