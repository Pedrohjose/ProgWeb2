"""Testes isolados de HTTP e persistência com SQLite; MySQL é verificado no PC."""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from banco import Base, get_db
from main import app
from models import Usuario, Tarefa, ItensTarefa, Item, Localizacao
from datetime import date

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        def session():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = session
        self.client = TestClient(app)
        self.payload = dict(nome='João Teste',email='joao@example.com',senha='TesteLocal123!',perfil='Funcionario')
    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()
    def test_swagger(self):
        self.assertEqual(self.client.get('/docs').status_code,200)
        schema = self.client.get('/openapi.json').json()
        esperadas = {
            ('post','/login'),
            ('get','/tarefas/all'),('get','/tarefas/{id}'),('post','/tarefas'),('put','/tarefas/{id}'),
            ('delete','/tarefas/{id}'),('put','/tarefas/{id}/atribuir/{usuarioId}'),
            ('get','/usuarios/all'),('get','/usuarios/{id}'),('post','/usuarios'),('put','/usuarios/{id}'),
            ('delete','/usuarios/{id}'),('get','/usuarios/{id}/tarefas/all'),
            ('get','/localizacoes/all'),('get','/localizacoes/{id}'),('post','/localizacoes'),
            ('put','/localizacoes/{id}'),('delete','/localizacoes/{id}'),
            ('get','/localizacoes/{id}/itens/all'),('get','/localizacoes/{id}/qrcode/all'),
        }
        methods = {'get', 'post', 'put', 'delete'}
        obtidas = {(m, p) for p, ops in schema['paths'].items() if not p.startswith('/saude') for m in set(ops) & methods}
        self.assertEqual(obtidas, esperadas)
        self.assertEqual(len(obtidas), 20)
        self.assertEqual({'/saude', '/saude/banco'}, {p for p in schema['paths'] if p.startswith('/saude')})
        self.assertIn('409',schema['paths']['/usuarios']['post']['responses'])
        self.assertEqual(schema['info']['title'], 'ESTOK — Swagger de Testes')
        for p, ops in schema['paths'].items():
            for m in set(ops) & methods:
                self.assertTrue(ops[m].get('summary') and ops[m].get('tags'), f'{m} {p} sem summary/tag no Swagger')
        self.assertNotIn('content', schema['paths']['/usuarios/{id}']['delete']['responses']['204'])
        self.assertNotIn('content', schema['paths']['/tarefas/{id}']['delete']['responses']['204'])
        self.assertNotIn('content', schema['paths']['/localizacoes/{id}']['delete']['responses']['204'])
    def test_fluxo_usuario(self):
        result=self.client.post('/usuarios',json=self.payload)
        self.assertEqual(result.status_code,201,result.text)
        uid=result.json()['id']
        self.assertNotIn('senha',result.json())
        with self.sessions() as db:
            self.assertNotEqual(db.get(Usuario,uid).senha,self.payload['senha'])
        self.assertEqual(self.client.post('/usuarios',json=self.payload).status_code,409)
        login={k:self.payload[k] for k in ('email','senha')}
        self.assertEqual(self.client.post('/login',json=login).status_code,200)
        self.assertEqual(self.client.post('/login',json={**login,'senha':'errada'}).status_code,401)
        updated={**self.payload,'nome':'Nome atualizado','senha':'NovaSenha123!'}
        self.assertEqual(self.client.put(f'/usuarios/{uid}',json=updated).status_code,200)
        self.assertEqual(self.client.post('/login',json=login).status_code,401)
        self.assertEqual(self.client.post('/login',json={**login,'senha':updated['senha']}).status_code,200)
        self.assertEqual(self.client.put('/usuarios/999',json=updated).status_code,404)
    def test_validacao(self):
        self.assertEqual(self.client.post('/usuarios',json={**self.payload,'email':'invalido'}).status_code,422)
        self.assertEqual(self.client.post('/usuarios',json={**self.payload,'perfil':'invalido'}).status_code,422)
    def test_banco_indisponivel(self):
        def falha():
            raise OperationalError('SELECT 1',{},Exception('segredo interno'))
        app.dependency_overrides[get_db]=falha
        result=self.client.get('/saude/banco')
        self.assertEqual(result.status_code,503)
        self.assertNotIn('segredo',result.text)
    def test_saude(self):
        self.assertEqual(self.client.get('/saude').status_code,200)
        self.assertEqual(self.client.get('/saude/banco').status_code,200)

    def test_listar_consultar_excluir(self):
        self.assertEqual(self.client.get('/usuarios/all').json(), [])
        created = self.client.post('/usuarios', json=self.payload).json()
        uid = created['id']
        self.assertEqual(self.client.get('/usuarios/all').json(), [created])
        found = self.client.get(f'/usuarios/{uid}')
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json(), created)
        self.assertNotIn('senha', found.json())
        removed = self.client.delete(f'/usuarios/{uid}')
        self.assertEqual(removed.status_code, 204)
        self.assertEqual(removed.content, b'')
        self.assertEqual(self.client.get(f'/usuarios/{uid}').status_code, 404)
        self.assertEqual(self.client.delete(f'/usuarios/{uid}').status_code, 404)
        self.assertEqual(self.client.get('/usuarios/all').json(), [])
        self.assertEqual(self.client.post('/login', json={'email':self.payload['email'], 'senha':self.payload['senha']}).status_code, 401)
        with self.sessions() as db:
            self.assertIsNone(db.get(Usuario, uid))

    def test_id_invalido(self):
        for method in ('get', 'delete'):
            self.assertEqual(getattr(self.client, method)('/usuarios/abc').status_code, 422)
            self.assertEqual(getattr(self.client, method)('/usuarios/-1').status_code, 404)

    def test_exclusao_preserva_usuario_com_tarefas(self):
        uid = self.client.post('/usuarios', json=self.payload).json()['id']
        with self.sessions() as db:
            db.add(Tarefa(tituto='Tarefa vinculada', prazo=date(2026,12,1), statusTarefas='Pendante', id_usuario=uid))
            db.commit()
        self.assertEqual(self.client.delete(f'/usuarios/{uid}').status_code, 409)
        self.assertEqual(self.client.get(f'/usuarios/{uid}').status_code, 200)
        with self.sessions() as db:
            self.assertIsNotNone(db.scalar(select(Tarefa).where(Tarefa.id_usuario == uid)))

    def test_atualizacao_conflitante_preserva_cadastro(self):
        uid = self.client.post('/usuarios', json=self.payload).json()['id']
        outro = {**self.payload, 'email':'outro@example.com'}
        self.client.post('/usuarios', json=outro)
        self.assertEqual(self.client.put(f'/usuarios/{uid}', json=outro).status_code, 409)
        self.assertEqual(self.client.get(f'/usuarios/{uid}').json()['email'], self.payload['email'])

    # ---------- Tarefas ----------
    def criar_usuario(self, email='func@example.com'):
        return self.client.post('/usuarios', json={**self.payload, 'email': email}).json()['id']

    def test_fluxo_tarefas(self):
        uid = self.criar_usuario()
        corpo = {'titulo': 'Conferir estoque', 'descricao': 'Mensal', 'prazo': '2026-12-01'}
        criada = self.client.post('/tarefas', json=corpo)
        self.assertEqual(criada.status_code, 201, criada.text)
        tarefa = criada.json()
        self.assertEqual((tarefa['titulo'], tarefa['status'], tarefa['id_usuario']), ('Conferir estoque', 'Pendante', None))
        self.assertNotIn('tituto', tarefa)
        with self.sessions() as db:
            self.assertEqual(db.get(Tarefa, tarefa['id']).tituto, 'Conferir estoque')
        self.assertEqual(self.client.post('/tarefas', json=corpo).status_code, 409)
        self.assertEqual(self.client.post('/tarefas', json={**corpo, 'titulo': 'Outra', 'id_usuario': 999}).status_code, 404)
        self.assertEqual(self.client.get('/tarefas/all').json(), [tarefa])
        self.assertEqual(self.client.get(f"/tarefas/{tarefa['id']}").json(), tarefa)
        edit = self.client.put(f"/tarefas/{tarefa['id']}", json={**corpo, 'descricao': 'Nova', 'status': 'Em_Andamento'})
        self.assertEqual(edit.status_code, 200, edit.text)
        self.assertEqual((edit.json()['descricao'], edit.json()['status']), ('Nova', 'Em_Andamento'))
        self.assertEqual(self.client.get('/usuarios/%d/tarefas/all' % uid).json(), [])
        atribuida = self.client.put(f"/tarefas/{tarefa['id']}/atribuir/{uid}")
        self.assertEqual(atribuida.status_code, 200, atribuida.text)
        self.assertEqual(atribuida.json()['id_usuario'], uid)
        self.assertEqual([t['id'] for t in self.client.get('/usuarios/%d/tarefas/all' % uid).json()], [tarefa['id']])
        self.assertEqual(self.client.put(f"/tarefas/{tarefa['id']}/atribuir/999").status_code, 404)
        self.assertEqual(self.client.put(f"/tarefas/999/atribuir/{uid}").status_code, 404)
        self.assertEqual(self.client.get('/usuarios/999/tarefas/all').status_code, 404)
        removed = self.client.delete(f"/tarefas/{tarefa['id']}")
        self.assertEqual((removed.status_code, removed.content), (204, b''))
        self.assertEqual(self.client.get(f"/tarefas/{tarefa['id']}").status_code, 404)
        self.assertEqual(self.client.delete(f"/tarefas/{tarefa['id']}").status_code, 404)
        self.assertEqual(self.client.get(f'/usuarios/{uid}').status_code, 200)

    def test_tarefas_validacao_e_conflitos(self):
        corpo = {'titulo': 'A', 'prazo': '2026-12-01'}
        self.assertEqual(self.client.post('/tarefas', json={'titulo': ''}).status_code, 422)
        self.assertEqual(self.client.post('/tarefas', json={**corpo, 'prazo': '31/12/2026'}).status_code, 422)
        self.assertEqual(self.client.post('/tarefas', json={**corpo, 'status': 'Inventado'}).status_code, 422)
        self.assertEqual(self.client.get('/tarefas/abc').status_code, 422)
        self.assertEqual(self.client.get('/tarefas/-1').status_code, 404)
        self.assertEqual(self.client.get('/tarefas/all').json(), [])
        a = self.client.post('/tarefas', json=corpo).json()
        b = self.client.post('/tarefas', json={**corpo, 'titulo': 'B'}).json()
        self.assertEqual(self.client.put(f"/tarefas/{b['id']}", json={**corpo, 'titulo': 'A', 'status': 'Concluida'}).status_code, 409)
        self.assertEqual(self.client.get(f"/tarefas/{b['id']}").json()['titulo'], 'B')
        self.assertEqual(self.client.put('/tarefas/999', json={**corpo, 'status': 'Concluida'}).status_code, 404)
        self.assertEqual(a['status'], 'Pendante')

    def test_exclusao_tarefa_preserva_itens(self):
        tarefa = self.client.post('/tarefas', json={'titulo': 'Com itens', 'prazo': '2026-12-01'}).json()
        with self.sessions() as db:
            vinculo = ItensTarefa(statusItemTarefa='Pendente', dataConferencia=date(2026, 12, 1), id_tarefa=tarefa['id'])
            db.add(vinculo)
            db.flush()
            db.add(Item(codigoUnico='PAT-1', nome='Notebook', id_itemTarefa=vinculo.id))
            db.commit()
        self.assertEqual(self.client.delete(f"/tarefas/{tarefa['id']}").status_code, 409)
        self.assertEqual(self.client.get(f"/tarefas/{tarefa['id']}").status_code, 200)
        with self.sessions() as db:
            self.assertIsNotNone(db.scalar(select(Item).where(Item.codigoUnico == 'PAT-1')))

    # ---------- Localizações ----------
    LOC = dict(nome='Almoxarifado', cep='01310100', logradouro='Av. Paulista', numero='1000', bairro='Bela Vista',
               cidade='São Paulo', estado='sp')

    def test_fluxo_localizacoes(self):
        criada = self.client.post('/localizacoes', json={**self.LOC, 'latitude': -23.5614, 'longitude': -46.6559})
        self.assertEqual(criada.status_code, 201, criada.text)
        loc = criada.json()
        self.assertEqual((loc['estado'], loc['tipo_endereco'], loc['principal']), ('SP', 'Entrega', False))
        self.assertAlmostEqual(loc['latitude'], -23.5614, places=4)
        self.assertEqual(self.client.get('/localizacoes/all').json(), [loc])
        self.assertEqual(self.client.get(f"/localizacoes/{loc['id']}").json(), loc)
        up = self.client.put(f"/localizacoes/{loc['id']}", json={**self.LOC, 'nome': 'Depósito', 'tipo_endereco': 'Comercial', 'principal': True})
        self.assertEqual(up.status_code, 200, up.text)
        self.assertEqual((up.json()['nome'], up.json()['tipo_endereco'], up.json()['principal'], up.json()['latitude']), ('Depósito', 'Comercial', True, None))
        self.assertEqual(self.client.put('/localizacoes/999', json=self.LOC).status_code, 404)
        removed = self.client.delete(f"/localizacoes/{loc['id']}")
        self.assertEqual((removed.status_code, removed.content), (204, b''))
        self.assertEqual(self.client.get(f"/localizacoes/{loc['id']}").status_code, 404)
        self.assertEqual(self.client.delete(f"/localizacoes/{loc['id']}").status_code, 404)

    def test_localizacoes_validacao(self):
        for ruim in ({'cep': '123'}, {'cep': '0131010a'}, {'estado': 'SPP'}, {'latitude': 91}, {'longitude': -181},
                     {'tipo_endereco': 'Casa'}, {'nome': ''}):
            self.assertEqual(self.client.post('/localizacoes', json={**self.LOC, **ruim}).status_code, 422, ruim)
        self.assertEqual(self.client.get('/localizacoes/abc').status_code, 422)
        self.assertEqual(self.client.get('/localizacoes/-1').status_code, 404)

    def test_itens_qrcode_e_exclusao_com_itens(self):
        loc = self.client.post('/localizacoes', json=self.LOC).json()
        vazia = self.client.post('/localizacoes', json=self.LOC).json()
        self.assertEqual(self.client.get(f"/localizacoes/{loc['id']}/itens/all").json(), [])
        self.assertEqual(self.client.get(f"/localizacoes/{loc['id']}/qrcode/all").json(), [])
        with self.sessions() as db:
            db.add_all([Item(codigoUnico='PAT-1', nome='Notebook', id_localizacao=loc['id']),
                        Item(codigoUnico='PAT-2', nome='Monitor', id_localizacao=loc['id']),
                        Item(codigoUnico='PAT-3', nome='Outro lugar', id_localizacao=vazia['id'])])
            db.commit()
        itens = self.client.get(f"/localizacoes/{loc['id']}/itens/all")
        self.assertEqual(itens.status_code, 200)
        self.assertEqual([i['codigoUnico'] for i in itens.json()], ['PAT-1', 'PAT-2'])
        qr = self.client.get(f"/localizacoes/{loc['id']}/qrcode/all")
        self.assertEqual(qr.status_code, 200)
        self.assertEqual([q['codigoUnico'] for q in qr.json()], ['PAT-1', 'PAT-2'])
        self.assertTrue(all(q['qrcode'].startswith('data:image/svg+xml') for q in qr.json()))
        self.assertEqual(self.client.get('/localizacoes/999/itens/all').status_code, 404)
        self.assertEqual(self.client.get('/localizacoes/999/qrcode/all').status_code, 404)
        self.assertEqual(self.client.delete(f"/localizacoes/{loc['id']}").status_code, 409)
        with self.sessions() as db:
            self.assertEqual(len(db.scalars(select(Item)).all()), 3)

    # ---------- Collection do Postman ----------
    def test_sequencia_collection(self):
        """Reproduz a Collection inteira contra a API e confere os códigos HTTP declarados em cada teste."""
        import json
        import re
        import uuid
        from pathlib import Path
        collection = json.loads(Path(__file__).with_name('ESTOK.postman_collection.json').read_text(encoding='utf-8'))
        self.assertEqual(collection['info']['name'], 'ESTOK API')
        self.assertEqual([p['name'] for p in collection['item']],
                         ['Diagnóstico', 'Autenticação', 'Usuários', 'Localizações', 'Tarefas - Gestão'])
        values = {v['key']: v['value'] for v in collection['variable']}
        values['base_url'] = ''
        def render(text):
            return re.sub(r'\{\{(\w+)\}\}', lambda m: str(values[m.group(1)]), text)
        def script(item, evento):
            return next((e['script']['exec'] for e in item['event'] if e['listen'] == evento), [])
        cobertos = set()
        executadas = 0
        for pasta in collection['item']:
            for item in pasta['item']:
                request = item['request']
                for linha in script(item, 'prerequest'):
                    guid = re.fullmatch(r'pm\.collectionVariables\.set\("(\w+)", "([^"]*)" \+ pm\.variables\.replaceIn\("\{\{\$guid\}\}"\)(?: \+ "([^"]*)")?\);', linha)
                    fixo = re.fullmatch(r'pm\.collectionVariables\.set\("(\w+)", "([^"]*)"\);', linha)
                    if guid:
                        values[guid.group(1)] = guid.group(2) + str(uuid.uuid4()) + (guid.group(3) or '')
                    elif fixo:
                        values[fixo.group(1)] = fixo.group(2)
                    else:
                        self.fail('Pré-script não reconhecido: ' + linha)
                body = json.loads(render(request['body']['raw'])) if 'body' in request else None
                url = render(request['url'])
                response = self.client.request(request['method'], url, json=body)
                teste = ' '.join(script(item, 'test'))
                esperado = int(re.search(r'to\.have\.status\((\d+)\)', teste).group(1))
                self.assertEqual(response.status_code, esperado, f"{pasta['name']} / {item['name']}: {response.text}")
                if response.status_code == 204:
                    self.assertEqual(response.content, b'')
                for var, campo in re.findall(r'collectionVariables\.set\("(\w+)", pm\.response\.json\(\)\.(\w+)\)', teste):
                    values[var] = response.json()[campo]
                bruto = request['url'].replace('{{base_url}}', '')
                cobertos.add((request['method'].lower(), re.sub(r'/(\{\{\w+\}\}|-?\d+|abc)', '/{}', bruto)))
                executadas += 1
        self.assertGreaterEqual(executadas, 20)
        schema = self.client.get('/openapi.json').json()
        api = {(m, re.sub(r'\{\w+\}', '{}', p)) for p, ops in schema['paths'].items() for m in ops}
        self.assertEqual(api - cobertos, set(), 'Endpoints sem requisição na Collection')
        with self.sessions() as db:
            for model in (Usuario, Tarefa, Localizacao):
                self.assertEqual(db.scalars(select(model)).all(), [], f'{model.__name__} de teste não foi limpo')

if __name__ == '__main__':
    unittest.main()
