"""Cria somente o banco de desenvolvimento e recusa schemas de outra origem."""
import re
from sqlalchemy import create_engine, inspect, text
from banco import DB_NAME, database_url, engine
if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
    raise SystemExit("DB_NAME inválido.")
if DB_NAME != "estok_joao":
    raise SystemExit("Este preparador usa somente estok_joao. Não aponte para bancos existentes do grupo.")
server = create_engine(database_url(None))
with server.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4"))
tables = inspect(engine).get_table_names()
if tables:
    if "alembic_version" not in tables:
        raise SystemExit("Banco já tem tabelas sem histórico Alembic. Pare e revise; nenhuma tabela foi apagada.")
    with engine.connect() as conn:
        revisions = list(conn.execute(text("SELECT version_num FROM alembic_version")).scalars())
    if revisions != ["joao_baseline_01"]:
        raise SystemExit("Histórico diferente ou migration incompleta. Pare e revise o banco.")
print("Banco de desenvolvimento preparado.")
