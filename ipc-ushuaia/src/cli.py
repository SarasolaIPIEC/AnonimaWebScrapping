"""
CLI para ejecución manual y automatizada del sistema.
Incluye plantilla para integración de comandos y scheduler.
"""

import argparse


def main():
	parser = argparse.ArgumentParser(description='IPC Ushuaia CLI')
	parser.add_argument('--run', action='store_true', help='Ejecutar flujo completo')
	parser.add_argument('--ae', type=float, default=1.0, help='Multiplicador de Adulto Equivalente')
	parser.add_argument('--export', choices=['csv', 'json', 'html'], help='Formato de exportación')
	parser.add_argument('--cba-csv', type=str, default='ipc-ushuaia/data/cba_catalog.csv', help='Ruta al catálogo CBA')
	parser.add_argument('--output', type=str, default='ipc-ushuaia/exports/serie_cba', help='Ruta base de exportación')
	args = parser.parse_args()

	if args.run:
		print(f"Ejecutando IPC Ushuaia para AE={args.ae} y export={args.export}")
		import sys, os
		sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
		from normalizer import load_cba_catalog, adjust_quantities
		from metrics.cba import compute_cba_ae
		from db import repo
		from exporter import export_to_csv, export_to_json, export_to_html
		from datetime import date
		import pandas as pd

		# 1. Cargar catálogo CBA
		cba_catalog = load_cba_catalog(args.cba_csv)
		adjusted = adjust_quantities(cba_catalog, args.ae)

		# 2. [Simulación] Cargar precios scrapeados (debería venir del scraper)
		basket = pd.DataFrame([
			{'sku': row['item'], 'quantity': row['adjusted_qty']} for row in adjusted if row['adjusted_qty']
		])
		prices = pd.DataFrame([
			{'sku': row['item'], 'unit_price': 100 + i*10} for i, row in enumerate(adjusted) if row['adjusted_qty']
		])

		# 3. Calcular CBA
		cba_total = compute_cba_ae(prices, basket)
		print(f"Costo total CBA AE={args.ae}: {cba_total:.2f}")

		# 4. Persistir resultados (ejemplo: insertar run, precios, índice)
		run_id = repo.insert_run(date.today(), 'Ushuaia', 'ok')
		for i, row in prices.iterrows():
			sku_id = repo.insert_sku(1, row['sku'], row['sku'], 1, 'kg')  # Simulado
			repo.insert_price(sku_id, run_id, row['unit_price'], None, True)
		repo.insert_index_value(run_id, cba_total, cba_total, 100, 0, 0)

		# 5. Exportar resultados
		if args.export == 'csv':
			export_to_csv(prices, args.output + '.csv')
		elif args.export == 'json':
			export_to_json(prices, args.output + '.json')
		elif args.export == 'html':
			export_to_html(prices, args.output + '.html')
		print(f"Exportación completada en {args.output}.{args.export}")
	else:
		parser.print_help()

if __name__ == '__main__':
	main()
