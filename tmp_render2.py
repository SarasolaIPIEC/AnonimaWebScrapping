

"""
Script de demo para renderizado rápido de reportes IPC Ushuaia.

Lee insumos (series y breakdown) y genera el HTML mensual usando la función principal del pipeline.
Permite parametrizar rutas y período por CLI o variables de entorno.
Incluye logging y manejo robusto de errores.
"""

import sys
import logging
from src.reporting.render import render_report



def main():
	"""
	Ejecuta el renderizado del reporte HTML IPC Ushuaia.
	Permite parametrizar rutas y período por CLI o variables de entorno.
	Registra logs informativos y errores.
	"""
	import argparse
	import os
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s [%(levelname)s] %(message)s",
		handlers=[logging.StreamHandler(sys.stdout)]
	)
	parser = argparse.ArgumentParser(description="Renderiza el reporte HTML IPC Ushuaia.")
	parser.add_argument('--period', type=str, default=os.getenv('IPC_PERIOD', '2025-09'), help='Período YYYY-MM')
	parser.add_argument('--series', type=str, default=os.getenv('IPC_SERIES', 'exports/series_cba.csv'), help='Ruta a series_cba.csv')
	parser.add_argument('--breakdown', type=str, default=os.getenv('IPC_BREAKDOWN', 'exports/breakdown_2025-09.csv'), help='Ruta a breakdown_<period>.csv')
	parser.add_argument('--output', type=str, default=os.getenv('IPC_OUTPUT', 'reports/2025-09.html'), help='Ruta de salida del HTML')
	args = parser.parse_args()

	# Renderiza el reporte HTML usando los insumos y parámetros provistos
	try:
		render_report(args.output, args.period, args.series, args.breakdown)
		logging.info(f'Reporte renderizado correctamente: {args.output}')
	except FileNotFoundError as e:
		logging.error(f"Archivo no encontrado: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Error inesperado al renderizar reporte: {e}")
		sys.exit(99)

if __name__ == "__main__":
	main()
