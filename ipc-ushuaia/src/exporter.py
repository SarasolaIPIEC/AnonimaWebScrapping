"""
Exportador de datos a CSV, HTML y JSON.
TODO: Implementar funciones de exportación y compatibilidad Power BI.
"""

# TODO: Definir funciones de exportación
import pandas as pd

def export_to_csv(df: pd.DataFrame, path: str):
	"""
	Exporta un DataFrame a CSV.
	"""
	df.to_csv(path, index=True)

def export_to_json(df: pd.DataFrame, path: str):
	"""
	Exporta un DataFrame a JSON.
	"""
	df.to_json(path, orient='records', force_ascii=False)

def export_to_html(df: pd.DataFrame, path: str):
	"""
	Exporta un DataFrame a HTML.
	"""
	df.to_html(path, index=True)

# TODO: Integrar con index_engine.py y report.py para automatizar salidas
