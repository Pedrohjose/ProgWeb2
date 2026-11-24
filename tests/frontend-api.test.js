import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test, beforeEach, afterEach } from 'node:test';

// O Vite fornece import.meta.env; os testes executam o mesmo cliente em Node.
const fonte = (await readFile(new URL('../src/listagens-api.js', import.meta.url), 'utf8'))
  .replace('import.meta.env.VITE_API_BASE_URL', "'/api'");
const { cadastrar, listar, solicitar, ErroAPI } = await import(`data:text/javascript;base64,${Buffer.from(fonte).toString('base64')}`);
const fetchOriginal = globalThis.fetch;
const storageOriginal = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage');

beforeEach(() => {
  const dados = new Map([['estok.accessToken', 'access-antigo'], ['estok.refreshToken', 'refresh-antigo']]);
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: {
    getItem: key => dados.get(key) ?? null,
    setItem: (key, valor) => dados.set(key, valor),
    removeItem: key => dados.delete(key),
  } });
});
afterEach(() => {
  globalThis.fetch = fetchOriginal;
  if (storageOriginal) Object.defineProperty(globalThis, 'sessionStorage', storageOriginal);
  else delete globalThis.sessionStorage;
});

test('cadastro mantém corpo e método ao renovar um token expirado', async () => {
  const chamadas = [];
  globalThis.fetch = async (url, options) => {
    chamadas.push({ url, ...options });
    if (url === '/api/refresh') return Response.json({ access_token: 'access-novo', refresh_token: 'refresh-novo' });
    if (chamadas.length === 1) return Response.json({ detail: 'Expirado' }, { status: 401 });
    return Response.json({ id: 5, nome: 'Monitor' }, { status: 201 });
  };
  const dados = { nome: 'Monitor', codigoUnico: 'MON-005', id_localizacao: null };
  assert.equal((await cadastrar('/itens', dados)).id, 5);
  assert.deepEqual(chamadas.map(c => c.url), ['/api/itens', '/api/refresh', '/api/itens']);
  assert.equal(chamadas[2].method, 'POST');
  assert.deepEqual(JSON.parse(chamadas[2].body), dados);
  assert.equal(chamadas[2].headers.Authorization, 'Bearer access-novo');
  assert.equal(chamadas[2].headers['Content-Type'], 'application/json');
});

test('duplicidade conserva a mensagem da API e não repete o cadastro', async () => {
  let chamadas = 0;
  globalThis.fetch = async () => { chamadas++; return Response.json({ detail: 'Código já cadastrado' }, { status: 409 }); };
  await assert.rejects(cadastrar('/itens', {}), e => e instanceof ErroAPI && e.status === 409 && e.message === 'Código já cadastrado');
  assert.equal(chamadas, 1);
});

test('erros de validação identificam o campo rejeitado', async () => {
  globalThis.fetch = async () => Response.json({ detail: [{ loc: ['body', 'cep'], msg: 'CEP inválido' }] }, { status: 422 });
  await assert.rejects(cadastrar('/localizacoes', {}), e => e.status === 422 && e.message === 'cep: CEP inválido');
});

test('imagem do QR é recebida como blob com autenticação', async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/itens/5/qrcode');
    assert.equal(options.headers.Authorization, 'Bearer access-antigo');
    return new Response(new Uint8Array([137, 80, 78, 71]), { headers: { 'Content-Type': 'image/png' } });
  };
  const blob = await solicitar('/itens/5/qrcode', {}, 'blob');
  assert.equal(blob.type, 'image/png'); assert.equal(blob.size, 4);
});

test('logout com resposta 204 não exige JSON', async () => {
  globalThis.fetch = async () => new Response(null, { status: 204 });
  assert.equal(await cadastrar('/logout', { refresh_token: 'refresh-antigo' }), null);
});

test('sem sessão não envia chamadas e listagens recusam formato inválido', async () => {
  sessionStorage.removeItem('estok.accessToken');
  globalThis.fetch = async () => { assert.fail('Não deve consultar a API sem sessão'); };
  await assert.rejects(listar('/usuarios/all'), e => e.status === 401);
  sessionStorage.setItem('estok.accessToken', 'access');
  globalThis.fetch = async () => Response.json({ items: [] });
  await assert.rejects(listar('/usuarios/all'), /formato de lista inesperado/);
});
