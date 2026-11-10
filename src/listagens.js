import { listar } from './listagens-api.js';

const valor = v => v === null || v === undefined || v === '' ? '—' : String(v);
const texto = v => String(v ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const data = v => /^\d{4}-\d{2}-\d{2}/.test(v || '') ? v.slice(0, 10).split('-').reverse().join('/') : valor(v);
const status = v => ({ Pendante: 'Pendente', Em_Andamento: 'Em andamento', Concluida: 'Concluída' }[v] || valor(v));
const perfil = v => ({ Funcionario: 'Funcionário', Admin: 'Administrador', 'Super Admin': 'Super Admin' }[v] || valor(v));
const paginas = {
  usuarios: { endpoint: '/usuarios/all', filtro: 'Perfil', campo: 'perfil', rotulo: perfil,
    colunas: [['ID', 'id'], ['Nome', 'nome'], ['E-mail', 'email'], ['Perfil', r => perfil(r.perfil)]] },
  inventario: { endpoint: '/itens/all', filtro: 'Localização', campo: 'localizacao',
    colunas: [['ID', 'id'], ['Código único', 'codigoUnico'], ['Nome', 'nome'], ['Descrição', 'descricao'], ['Localização', 'localizacao']] },
  tarefa: { endpoint: '/tarefas/all', filtro: 'Status', campo: 'status', rotulo: status,
    colunas: [['ID', 'id'], ['Título', 'titulo'], ['Descrição', 'descricao'], ['Prazo', r => data(r.prazo)], ['Status', r => status(r.status)], ['Responsável', 'responsavel']] },
  localizacoes: { endpoint: '/localizacoes/all', filtro: 'Cidade', campo: 'cidade',
    colunas: [['ID', 'id'], ['Nome', 'nome'], ['CEP', r => String(r.cep || '').replace(/^(\d{5})(\d{3})$/, '$1-$2')], ['Logradouro', 'logradouro'], ['Número', 'numero'], ['Complemento', 'complemento'], ['Bairro', 'bairro'], ['Cidade', 'cidade'], ['UF', 'estado']] },
};
const config = paginas[document.body.dataset.pagina];
const el = id => document.getElementById(id);
let registros = [];
const celula = (tag, value, classe) => {
  const node = document.createElement(tag);
  node.textContent = valor(value); node.className = classe;
  return node;
};
for (const [titulo] of config.colunas) {
  const th = celula('th', titulo, 'px-6 py-4 text-xs font-semibold uppercase tracking-wider text-gray-400');
  th.scope = 'col'; el('colunas').append(th);
}
el('rotuloFiltro').textContent = config.filtro;
el('perfilSessao').textContent = sessionStorage.getItem('estok.perfil') ? `Perfil: ${perfil(sessionStorage.getItem('estok.perfil'))}` : 'Sessão não iniciada';
function renderizar() {
  const busca = texto(el('pesquisa').value);
  const filtro = el('filtro').value;
  const lista = registros.filter(r => (!filtro || valor(r[config.campo]) === filtro) &&
    config.colunas.some(([, campo]) => texto(typeof campo === 'function' ? campo(r) : r[campo]).includes(busca)));
  el('linhas').replaceChildren();
  for (const registro of lista) {
    const tr = document.createElement('tr'); tr.className = 'transition hover:bg-white/5';
    for (const [, campo] of config.colunas) {
      tr.append(celula('td', typeof campo === 'function' ? campo(registro) : registro[campo], 'px-6 py-4 text-gray-300'));
    }
    el('linhas').append(tr);
  }
  if (!lista.length) {
    const tr = document.createElement('tr');
    const td = celula('td', registros.length ? 'Nenhum registro corresponde aos filtros.' : 'Nenhum registro cadastrado.', 'px-6 py-10 text-center text-gray-400');
    td.colSpan = config.colunas.length; tr.append(td); el('linhas').append(tr);
  }
  el('contador').textContent = `${lista.length} de ${registros.length} registros`;
}
async function carregar() {
  el('atualizar').disabled = true; el('atualizar').textContent = 'Carregando…';
  el('entrar').hidden = true; el('linhas').replaceChildren();
  el('aviso').hidden = false; el('aviso').textContent = 'Carregando registros…';
  el('contador').textContent = 'Carregando…';
  el('pesquisa').disabled = true; el('filtro').disabled = true;
  try {
    registros = await listar(config.endpoint);
    let aviso = '';
    if (document.body.dataset.pagina === 'inventario') {
      let nomes = new Map();
      if (registros.some(r => r.id_localizacao != null)) {
        try { nomes = new Map((await listar('/localizacoes/all')).map(r => [r.id, r.nome])); }
        catch { aviso = 'Itens carregados. Algumas localizações estão identificadas pelo ID.'; }
      }
      registros = registros.map(r => ({ ...r, localizacao: r.id_localizacao == null ? 'Sem localização' : nomes.get(r.id_localizacao) || `Localização #${r.id_localizacao}` }));
    }
    if (document.body.dataset.pagina === 'tarefa') {
      let nomes = new Map();
      const papel = sessionStorage.getItem('estok.perfil');
      if (['Admin', 'Super Admin'].includes(papel) && registros.some(r => r.id_usuario != null)) {
        try { nomes = new Map((await listar('/usuarios/all')).map(r => [r.id, r.nome])); }
        catch { aviso = 'Tarefas carregadas. Alguns responsáveis estão identificados pelo ID.'; }
      }
      registros = registros.map(r => ({ ...r, responsavel: r.id_usuario == null ? 'Sem responsável' : nomes.get(r.id_usuario) || `Usuário #${r.id_usuario}` }));
    }
    const anterior = el('filtro').value;
    el('filtro').replaceChildren(new Option('Todos', ''));
    for (const v of [...new Set(registros.map(r => valor(r[config.campo])))].sort((a,b) => a.localeCompare(b, 'pt-BR'))) {
      el('filtro').add(new Option(config.rotulo ? config.rotulo(v) : v, v));
    }
    if ([...el('filtro').options].some(o => o.value === anterior)) el('filtro').value = anterior;
    el('aviso').textContent = aviso; el('aviso').hidden = !aviso;
    el('pesquisa').disabled = false; el('filtro').disabled = false;
    renderizar();
  } catch (error) {
    registros = []; el('aviso').textContent = error.message;
    el('entrar').hidden = error.status !== 401;
    el('contador').textContent = 'Lista não carregada';
  } finally { el('atualizar').disabled = false; el('atualizar').textContent = 'Atualizar lista'; }
}
el('pesquisa').addEventListener('input', renderizar);
el('filtro').addEventListener('change', renderizar);
el('atualizar').addEventListener('click', carregar);
carregar();
