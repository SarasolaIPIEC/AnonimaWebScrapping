"""
Motor de cálculo de CBA, AE, familia tipo, índice base=100 y variaciones.
Incluye lógica de cálculo, actualización de serie histórica y validaciones automáticas.
"""

import pandas as pd
from typing import List, Dict, Any

def calculate_cba(adjusted_catalog: List[Dict[str, Any]], sku_prices: Dict[str, float]) -> float:
	"""
	Calcula el costo total de la CBA ajustada por AE/familia, usando los precios de los SKUs mapeados.
	Si falta precio para algún ítem, lo ignora y lo reporta por separado.
	"""
	total = 0.0
	missing = []
	for row in adjusted_catalog:
		item = row['item']
		qty = row.get('adjusted_qty')
		price = sku_prices.get(item)
		if qty is not None and price is not None:
			total += float(qty) * float(price)
		else:
			missing.append(item)
	return total, missing


def cba_totals(costs: Dict[str, float]) -> Dict[str, float]:
	"""Suma costos por ítem y calcula CBA para AE y familia tipo."""
	total_ae = sum(costs.values())
	return {
	'cba_ae': total_ae,
	'cba_familia': total_ae * 3.09,
	}

def calculate_index(series: pd.Series, base_period: str) -> pd.Series:
	"""
	Calcula el índice base=100 para la serie histórica de CBA.
	"""
	base_value = series.loc[base_period]
	return (series / base_value) * 100

def calculate_variations(index_series: pd.Series) -> pd.DataFrame:
	"""
	Calcula variaciones mensuales (m/m) e interanuales (i.a.) del índice.
	"""
	df = pd.DataFrame({'index': index_series})
	df['var_mm'] = df['index'].pct_change() * 100
	df['var_ia'] = df['index'].pct_change(12) * 100
	return df


def update_index_series(series: pd.Series, period: str, cba_ae: float, base_period: str) -> pd.DataFrame:
	"""Actualiza la serie de CBA con un nuevo período y calcula índice y variaciones."""
	updated = series.copy()
	updated.loc[period] = cba_ae
	updated = updated.sort_index()
	index = calculate_index(updated, base_period)
	return calculate_variations(index)

def validate_series(df: pd.DataFrame) -> Dict[str, Any]:
	"""
	Valida integridad de la serie histórica: valores nulos, outliers, gaps temporales.
	"""
	summary = {
		'missing': df.isnull().sum().to_dict(),
		'outliers': df[(df['index'] > df['index'].mean() + 3*df['index'].std())].index.tolist(),
		'gaps': df.index.to_series().diff().dt.days.gt(40).sum() if hasattr(df.index, 'to_series') else None
	}
	return summary

# TODO: Integrar con exporter.py para salida CSV/HTML/JSON y con normalizer.py para validaciones
