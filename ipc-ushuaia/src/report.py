"""
Generador de reportes automáticos y visualizaciones.
Incluye plantillas para resúmenes, gráficos y compatibilidad con Power BI.
"""

import pandas as pd

def generate_summary_report(df: pd.DataFrame) -> str:
	"""
	Genera un resumen textual de la CBA, índice y variaciones.
	"""
	resumen = f"Resumen CBA: media={df['index'].mean():.2f}, última={df['index'].iloc[-1]:.2f}"
	return resumen

# TODO: Agregar funciones para gráficos y visualizaciones
