
"""
Repositorio legacy para datos históricos en CSV/SQLite.
No se usa en el flujo principal (que usa PostgreSQL).
Marcar para eliminar si no se requiere compatibilidad legacy.
"""

import pandas as pd
import sqlite3
from typing import Optional

def load_historical_data(csv_path: Optional[str] = None, sqlite_path: Optional[str] = None, table: str = 'cba_history') -> pd.DataFrame:
	"""
	Carga datos históricos desde CSV o SQLite.
	"""
	if csv_path:
		return pd.read_csv(csv_path, parse_dates=True, index_col=0)
	elif sqlite_path:
		conn = sqlite3.connect(sqlite_path)
		df = pd.read_sql(f'SELECT * FROM {table}', conn, index_col='date', parse_dates=['date'])
		conn.close()
		return df
	else:
		raise ValueError('Debe especificar csv_path o sqlite_path')

def save_historical_data(df: pd.DataFrame, csv_path: Optional[str] = None, sqlite_path: Optional[str] = None, table: str = 'cba_history'):
	"""
	Guarda datos históricos en CSV o SQLite.
	"""
	if csv_path:
		df.to_csv(csv_path)
	if sqlite_path:
		conn = sqlite3.connect(sqlite_path)
		df.to_sql(table, conn, if_exists='replace')
		conn.close()


# [LEGACY] No mantener ni extender salvo requerimiento explícito.
