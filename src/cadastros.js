import { cadastrar, listar, solicitar } from './listagens-api.js';
import './cadastros.css';

const pagina = document.body.dataset.pagina;
const papel = sessionStorage.getItem('estok.perfil');
const autenticado = Boolean(sessionStorage.getItem('estok.accessToken'));
const admin = autenticado && ['Admin', 'Super Admin'].includes(papel);
const definicoes = {
  usuarios: { titulo: 'Cadastrar usuário', endpoint: '/usuarios', botao: 'Novo usuário' },
  inventario: { titulo: 'Cadastrar item', endpoint: '/itens', botao: 'Adicionar item' },
  tarefa: { titulo: 'Criar tarefa', endpoint: '/tarefas', botao: 'Criar tarefa' },
  localizacoes: { titulo: 'Cadastrar localização', endpoint: '/localizacoes', botao: 'Nova localização' },
};

function botao(texto, acao, primario = false) {
  const b = document.createElement('button');
  b.type = 'button'; b.className = `estok-botao${primario ? ' estok-primario' : ''}`;
  b.textContent = texto; b.addEventListener('click', acao);
  return b;
}

function janela(titulo) {
  const dialog = document.createElement('dialog');
  dialog.className = 'estok-modal'; dialog.setAttribute('aria-labelledby', 'estok-modal-titulo');
  const h = document.createElement('h2'); h.id = 'estok-modal-titulo'; h.textContent = titulo;
  dialog.append(h);
  const aviso = document.createElement('p');
  aviso.className = 'estok-feedback'; aviso.setAttribute('role', 'status'); aviso.setAttribute('aria-live', 'polite');
  const fechar = botao('Cancelar', () => dialog.close());
  const acoes = document.createElement('div'); acoes.className = 'estok-acoes'; acoes.append(fechar);
  document.body.append(dialog);
  dialog.addEventListener('close', () => dialog.remove(), { once: true });
  return { dialog, aviso, acoes, fechar };
}

function campo(form, nome, rotulo, opts = {}) {
  const label = document.createElement('label'); label.className = `estok-campo${opts.amplo ? ' estok-amplo' : ''}`;
  const span = document.createElement('span'); span.textContent = rotulo + (opts.required ? ' *' : ' (opcional)');
  const input = document.createElement(opts.opcoes ? 'select' : opts.tipo === 'textarea' ? 'textarea' : 'input');
  input.name = nome; input.required = Boolean(opts.required);
  if (input.tagName === 'INPUT') input.type = opts.tipo || 'text';
  for (const prop of ['minLength', 'maxLength', 'pattern', 'autocomplete', 'min', 'max', 'step']) {
    if (opts[prop] !== undefined) input[prop] = opts[prop];
  }
  if (opts.opcoes) for (const [v, t] of opts.opcoes) input.add(new Option(t, v));
  label.append(span, input); form.append(label);
  return input;
}

const basico = { required: true, maxLength: 255 };
async function camposCadastro(form) {
  if (pagina === 'usuarios') {
    campo(form, 'nome', 'Nome', { ...basico, autocomplete: 'name' });
    campo(form, 'email', 'E-mail', { ...basico, tipo: 'email', autocomplete: 'email', minLength: 3 });
    campo(form, 'senha', 'Senha', { required: true, tipo: 'password', minLength: 8, maxLength: 128, autocomplete: 'new-password' });
    const perfis = [['Funcionario', 'Funcionário'], ['Admin', 'Administrador']];
    if (papel === 'Super Admin') perfis.push(['Super Admin', 'Super Admin']);
    campo(form, 'perfil', 'Perfil', { required: true, opcoes: perfis });
  } else if (pagina === 'inventario') {
    campo(form, 'nome', 'Nome', basico);
    campo(form, 'codigoUnico', 'Código único da etiqueta', basico);
    campo(form, 'descricao', 'Descrição', { tipo: 'textarea', maxLength: 255, amplo: true });
    const localizacoes = await listar('/localizacoes/all');
    campo(form, 'id_localizacao', 'Localização', { amplo: true, opcoes: [['', 'Sem localização'], ...localizacoes.map(l => [l.id, l.nome])] });
  } else if (pagina === 'tarefa') {
    campo(form, 'titulo', 'Título', { ...basico, amplo: true });
    campo(form, 'descricao', 'Descrição', { tipo: 'textarea', maxLength: 255, amplo: true });
    campo(form, 'prazo', 'Prazo', { required: true, tipo: 'date' });
    const usuarios = await listar('/usuarios/all');
    campo(form, 'id_usuario', 'Funcionário responsável', { opcoes: [['', 'Sem responsável'], ...usuarios.filter(u => u.perfil === 'Funcionario').map(u => [u.id, `${u.nome} — ${u.email}`])] });
    const nota = document.createElement('p'); nota.className = 'estok-amplo';
    nota.textContent = 'A tarefa será criada como pendente. Depois, use “Vincular item” na lista para escolher os patrimônios da conferência.'; form.append(nota);
  } else {
    campo(form, 'nome', 'Nome da localização', { ...basico, amplo: true });
    campo(form, 'cep', 'CEP (8 dígitos)', { required: true, pattern: '[0-9]{8}', maxLength: 8 });
    campo(form, 'estado', 'UF', { required: true, pattern: '[A-Za-z]{2}', maxLength: 2 });
    campo(form, 'logradouro', 'Logradouro', basico);
    campo(form, 'numero', 'Número', { required: true, maxLength: 20 });
    campo(form, 'bairro', 'Bairro', { required: true, maxLength: 100 });
    campo(form, 'cidade', 'Cidade', { required: true, maxLength: 100 });
    campo(form, 'complemento', 'Complemento', { maxLength: 100 });
    campo(form, 'tipo_endereco', 'Tipo de endereço', { required: true, opcoes: [['Entrega', 'Entrega'], ['Comercial', 'Comercial'], ['Residencial', 'Residencial'], ['Cobranca', 'Cobrança']] });
  }
}

function dadosFormulario(form) {
  const dados = Object.fromEntries(new FormData(form));
  for (const key of Object.keys(dados)) if (key !== 'senha') dados[key] = dados[key].trim();
  for (const key of ['id_usuario', 'id_localizacao']) if (key in dados) dados[key] = dados[key] ? Number(dados[key]) : null;
  for (const key of ['descricao', 'complemento']) if (key in dados && !dados[key]) dados[key] = null;
  if (dados.estado) dados.estado = dados.estado.toUpperCase();
  if (pagina === 'tarefa') dados.status = 'Pendante';
  return dados;
}

function formularioModal(titulo, salvar, atualizar, mensagem = 'Cadastro salvo com sucesso.') {
  const modal = janela(titulo);
  const form = document.createElement('form');
  const campos = document.createElement('div'); campos.className = 'estok-form';
  const submit = document.createElement('button'); submit.type = 'submit';
  submit.className = 'estok-botao estok-primario'; submit.textContent = 'Salvar'; submit.disabled = true;
  modal.acoes.append(submit); form.append(campos, modal.aviso, modal.acoes); modal.dialog.append(form);
  let enviando = false;
  modal.dialog.addEventListener('cancel', event => { if (enviando) event.preventDefault(); });
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (enviando || !form.reportValidity()) return;
    enviando = true; submit.disabled = true; modal.fechar.disabled = true; submit.textContent = 'Salvando…'; modal.aviso.textContent = '';
    try {
      await salvar(form);
      modal.dialog.close();
      await atualizar();
      let feedback = document.getElementById('cadastro-salvo');
      if (!feedback) {
        feedback = document.createElement('p'); feedback.id = 'cadastro-salvo';
        feedback.setAttribute('role', 'status'); feedback.className = 'mb-4 text-sm text-green-300';
        document.querySelector('main header').after(feedback);
      }
      feedback.textContent = mensagem;
    } catch (erro) {
      modal.aviso.textContent = erro.message;
    } finally {
      enviando = false; submit.disabled = false; modal.fechar.disabled = false; submit.textContent = 'Salvar';
    }
  });
  modal.aviso.textContent = 'Carregando opções…'; modal.dialog.showModal();
  return { ...modal, campos, submit };
}

async function abrirCadastro(atualizar) {
  const config = definicoes[pagina];
  const modal = formularioModal(config.titulo, form => cadastrar(config.endpoint, dadosFormulario(form)), atualizar);
  try {
    await camposCadastro(modal.campos);
    if (!modal.dialog.open) return;
    modal.aviso.textContent = ''; modal.submit.disabled = false;
    modal.campos.querySelector('input,select')?.focus();
  } catch (erro) { modal.aviso.textContent = `Não foi possível preparar o cadastro: ${erro.message} Feche e tente novamente.`; }
}

async function vincularItem(tarefa, atualizar) {
  const modal = formularioModal(`Vincular item — ${tarefa.titulo}`, form => {
    const item = new FormData(form).get('itemId');
    return cadastrar(`/tarefas/${tarefa.id}/itens/${encodeURIComponent(item)}`, {});
  }, atualizar, 'Item vinculado à tarefa com sucesso.');
  try {
    const itens = (await listar('/itens/all')).filter(i => i.id_itemTarefa == null);
    if (!modal.dialog.open) return;
    if (!itens.length) { modal.aviso.textContent = 'Nenhum item disponível. Cadastre um item no Inventário ou verifique os vínculos existentes.'; return; }
    campo(modal.campos, 'itemId', 'Item', { required: true, amplo: true, opcoes: [['', 'Selecione um item'], ...itens.map(i => [i.id, `${i.nome} — ${i.codigoUnico}`])] });
    modal.aviso.textContent = ''; modal.submit.disabled = false; modal.campos.querySelector('select').focus();
  } catch (erro) { modal.aviso.textContent = erro.message; }
}

async function verQRCode(item) {
  const modal = janela(`QR Code — ${item.nome}`); modal.dialog.classList.add('estok-qr');
  const codigo = document.createElement('code'); codigo.textContent = item.codigoUnico;
  const imagem = document.createElement('img'); imagem.alt = `QR Code do item ${item.nome}`; imagem.hidden = true;
  modal.fechar.textContent = 'Fechar'; modal.aviso.textContent = 'Carregando QR Code…';
  modal.dialog.append(codigo, imagem, modal.aviso, modal.acoes);
  let url;
  modal.dialog.addEventListener('close', () => { if (url) URL.revokeObjectURL(url); });
  modal.dialog.showModal();
  try {
    const blob = await solicitar(`/itens/${item.id}/qrcode`, {}, 'blob');
    if (!modal.dialog.open) return;
    if (blob.type.split(';')[0] !== 'image/png') throw new Error('A API não retornou uma imagem PNG válida.');
    url = URL.createObjectURL(blob);
    imagem.src = url;
    imagem.addEventListener('error', () => { imagem.hidden = true; modal.aviso.style.color = ''; modal.aviso.textContent = 'Não foi possível exibir a imagem do QR Code.'; });
    modal.aviso.style.color = '#9ca3af';
    imagem.hidden = false; modal.aviso.textContent = 'Este QR Code identifica o item pelo seu código único.';
    const baixar = document.createElement('a'); baixar.className = 'estok-botao estok-primario';
    baixar.textContent = 'Baixar PNG'; baixar.href = url; baixar.download = `qrcode-item-${item.id}.png`; modal.acoes.append(baixar);
  } catch (erro) { modal.aviso.textContent = erro.message; }
}

export function iniciarCadastros(atualizar) {
  if (!admin || !definicoes[pagina]) return;
  const header = document.querySelector('main header');
  const grupo = document.createElement('div'); grupo.className = 'flex flex-wrap gap-3';
  grupo.append(header.querySelector('#atualizar'), botao(definicoes[pagina].botao, () => abrirCadastro(atualizar), true));
  header.append(grupo);
}

export function temAcoes() { return autenticado && (pagina === 'inventario' || (pagina === 'tarefa' && admin)); }
export function acoesRegistro(registro, atualizar) {
  const td = document.createElement('td'); td.className = 'px-6 py-4';
  if (pagina === 'inventario') td.append(botao('Ver QR Code', () => verQRCode(registro)));
  if (pagina === 'tarefa' && admin) {
    const vincular = botao('Vincular item', () => vincularItem(registro, atualizar));
    vincular.disabled = registro.status === 'Concluida'; td.append(vincular);
  }
  return td;
}
