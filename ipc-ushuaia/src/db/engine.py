"""
Helper para conexión y migraciones en PostgreSQL.
"""
import psycopg2
import os

def get_connection():
    # TODO: Leer config de .env
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE", "ipc_ushuaia"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", 5432)
    )

def run_migration(sql_path):
    """
    Ejecuta un script SQL de migración.
    """
    with open(sql_path, encoding='utf-8') as f:
        sql = f.read()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    # TODO: Mejorar manejo de errores y logs
