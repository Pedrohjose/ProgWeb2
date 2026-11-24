// Sem configuração local, mantém o endereço da API da VM.
export const API_VM = import.meta.env.VITE_API_BASE_URL || 'http://40.127.11.169:8000';
export class ErroAPI extends Error {
  constructor(message, status = 0) { super(message); this.status = status; }
}
async function requisitar(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    return await fetch(`${API_VM}${path}`, { ...options, signal: controller.signal });
  } catch {
    throw new ErroAPI('Não foi possível conectar à API. Verifique se a VM está ligada e acessível e tente atualizar a lista.');
  } finally { clearTimeout(timeout); }
}
let renovacao;
async function renovar() {
  if (!renovacao) {
    renovacao = (async () => {
      const token = sessionStorage.getItem('estok.refreshToken');
      if (!token) return false;
      const response = await requisitar('/refresh', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: token }),
      });
      if (!response.ok) return false;
      const data = await response.json();
      if (!data.access_token || !data.refresh_token) return false;
      sessionStorage.setItem('estok.accessToken', data.access_token);
      sessionStorage.setItem('estok.refreshToken', data.refresh_token);
      return true;
    })().finally(() => { renovacao = undefined; });
  }
  return renovacao;
}
export async function solicitar(path, options = {}, formato = 'json') {
  if (!sessionStorage.getItem('estok.accessToken')) {
    throw new ErroAPI('Entre na sua conta para consultar os registros.', 401);
  }
  const enviar = () => requisitar(path, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${sessionStorage.getItem('estok.accessToken')}` },
  });
  let response = await enviar();
  if (response.status === 401 && await renovar()) response = await enviar();
  if (!response.ok) {
    const mensagens = {
      401: 'Sua sessão expirou. Entre novamente para consultar os registros.',
      403: 'Seu perfil não tem permissão para realizar esta operação.',
      404: 'O recurso solicitado não foi encontrado na API.',
      503: 'A API está disponível, mas o banco não respondeu. Tente novamente mais tarde.',
    };
    let detalhe;
    try {
      const erro = await response.json();
      detalhe = typeof erro.detail === 'string' ? erro.detail :
        Array.isArray(erro.detail) ? erro.detail.map(e => `${e.loc?.slice(1).join('.') || 'Campo'}: ${e.msg}`).join('; ') : null;
    } catch { /* Uma resposta sem JSON usa a mensagem de HTTP abaixo. */ }
    throw new ErroAPI(detalhe || mensagens[response.status] || `Não foi possível concluir a operação (HTTP ${response.status}).`, response.status);
  }
  if (response.status === 204) return null;
  if (formato === 'blob') return response.blob();
  let data;
  try { data = await response.json(); } catch { throw new ErroAPI('A API retornou uma resposta inválida.'); }
  return data;
}
export async function listar(path) {
  const data = await solicitar(path);
  if (!Array.isArray(data) || data.some(item => !item || typeof item !== 'object' || Array.isArray(item))) {
    throw new ErroAPI('A API retornou um formato de lista inesperado.');
  }
  return data;
}
export function cadastrar(path, dados) {
  return solicitar(path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados),
  });
}
