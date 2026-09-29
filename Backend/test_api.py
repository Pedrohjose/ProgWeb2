"""Testes isolados de HTTP e persistência com SQLite; MySQL é verificado no PC."""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from banco import Base, get_db
from main import app
from models import Usuario

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
        self.assertEqual(set(schema['paths']), {'/saude','/saude/banco','/login','/usuarios','/usuarios/{id}'})
        self.assertIn('409',schema['paths']['/usuarios']['post']['responses'])
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

if __name__ == '__main__':
    unittest.main()
