import { cadastrar } from './listagens-api.js';

if (document.getElementById('sessao-nome')) {
  let usuario;
  try { usuario = JSON.parse(sessionStorage.getItem('estok.usuario')); } catch { /* Sessão antiga ou inválida. */ }
  const conectado = Boolean(sessionStorage.getItem('estok.accessToken'));
  const nome = conectado && usuario?.nome ? usuario.nome : 'Entre novamente';
  document.getElementById('sessao-nome').textContent = nome;
  document.getElementById('sessao-email').textContent = conectado ? usuario?.email || '' : '';
  document.getElementById('sessao-perfil').textContent = conectado
    ? (usuario?.perfil || sessionStorage.getItem('estok.perfil') || '') : 'Sessão não iniciada';
  document.getElementById('sessao-iniciais').textContent = conectado && usuario?.nome
    ? usuario.nome.trim().split(/\s+/).filter(Boolean).filter((_, i, partes) => i === 0 || i === partes.length - 1).map(p => p[0]).join('').toUpperCase() : '?';
}

document.getElementById('sair')?.addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try {
    const refresh = sessionStorage.getItem('estok.refreshToken');
    if (refresh) await cadastrar('/logout', { refresh_token: refresh });
  } catch { /* Encerra a sessão local mesmo quando a API está indisponível. */ }
  finally {
    for (const chave of ['estok.accessToken', 'estok.refreshToken', 'estok.perfil', 'estok.usuario']) sessionStorage.removeItem(chave);
    window.location.replace('/index.html');
  }
});

