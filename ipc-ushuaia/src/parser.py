"""
Parser de HTML/JSON para extraer datos de productos y mapear a la CBA.
Incluye heurísticas de matching, reglas de sustitución y manejo de presentaciones.
"""

from typing import List, Dict, Any

# TODO: Implementar extracción real desde HTML/JSON de La Anónima

def match_sku_to_cba(product: Dict[str, Any], cba_row: Dict[str, Any]) -> bool:
	"""
	Heurística de matching por nombre, marca, tamaño y palabras clave.
	"""
	name = product.get('name', '').lower()
	preferred = [k.strip() for k in cba_row.get('preferred_keywords', '').split(';')]
	fallback = [k.strip() for k in cba_row.get('fallback_keywords', '').split(';')]
	for kw in preferred:
		if kw and kw in name:
			return True
	for kw in fallback:
		if kw and kw in name:
			return True
	return False


def map_products_to_cba(products: List[Dict[str, Any]], cba_catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
	"""
	Mapea productos scrapeados a los ítems de la CBA usando heurísticas y reglas de sustitución.
	Devuelve un dict: {item: {'sku':..., 'price':..., 'pack_size':...}}
	"""
	mapping = {}
	for cba_row in cba_catalog:
		matches = [p for p in products if match_sku_to_cba(p, cba_row)]
		if matches:
			# Elegir el SKU de menor precio por unidad
			best = min(matches, key=lambda x: x.get('unit_price', float('inf')))
			mapping[cba_row['item']] = {
				'sku': best.get('sku'),
				'price': best.get('unit_price'),
				'pack_size': best.get('pack_size'),
				'source': 'preferred' if any(kw in best.get('name', '').lower() for kw in cba_row.get('preferred_keywords', '').split(';')) else 'fallback'
			}
		else:
			mapping[cba_row['item']] = {'sku': None, 'price': None, 'pack_size': None, 'source': 'missing'}
	return mapping

# TODO: Documentar y testear reglas de sustitución y prorrateo
