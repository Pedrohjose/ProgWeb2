"""Testes isolados de HTTP e persistência com SQLite; MySQL é verificado no PC."""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from banco import Base, get_db
from main import app
from models import Usuario, Tarefa
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
        self.assertEqual(set(schema['paths']), {'/saude','/saude/banco','/login','/usuarios','/usuarios/{id}', '/usuarios/all'})
        self.assertIn('409',schema['paths']['/usuarios']['post']['responses'])
        self.assertEqual(schema['info']['title'], 'ESTOK — Swagger de Testes')
        methods = {'get', 'post', 'put', 'delete'}
        self.assertEqual(sum(len(set(ops) & methods) for path, ops in schema['paths'].items() if not path.startswith('/saude')), 6)
        self.assertNotIn('content', schema['paths']['/usuarios/{id}']['delete']['responses']['204'])
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

    def test_sequencia_collection(self):
        import json
        import re
        import uuid
        from pathlib import Path
        collection = json.loads(Path(__file__).with_name('ESTOK.postman_collection.json').read_text())
        values = {'email_teste':f'estok.{uuid.uuid4()}@example.com', 'usuario_id':'-1', 'base_url':''}
        expected = [200,200,201,409,200,401,200,200,200,200,422,404,422,204,404,404]
        self.assertEqual(len(collection['item']), len(expected))
        def render(text):
            for key, value in values.items():
                text = text.replace('{{'+key+'}}', str(value))
            return text
        for item, status in zip(collection['item'], expected):
            request = item['request']
            body = json.loads(render(request['body']['raw'])) if 'body' in request else None
            response = self.client.request(request['method'], render(request['url']), json=body)
            self.assertEqual(response.status_code, status, item['name'] + ': ' + response.text)
            script = next(e for e in item['event'] if e['listen']=='test')['script']['exec'][0]
            self.assertIn(f'status({status})', script)
            if response.status_code == 201:
                values['usuario_id'] = response.json()['id']
            if response.status_code == 200 and request['method']=='GET' and request['url'].endswith('/usuarios/{{usuario_id}}'):
                self.assertNotIn('senha', response.json())
                if item['name'].startswith('10'):
                    self.assertEqual(response.json()['nome'], 'Usuário Atualizado')
            if response.status_code == 204:
                self.assertEqual(response.content, b'')
        with self.sessions() as db:
            self.assertIsNone(db.get(Usuario, values['usuario_id']))

if __name__ == '__main__':
    unittest.main()
