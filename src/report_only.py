import sys
from src.reporting.render import render_report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Genera el reporte HTML sin scrapear.")
    parser.add_argument('--period', type=str, required=True, help='Período YYYY-MM')
    parser.add_argument('--series', type=str, default='exports/series_cba.csv', help='Ruta a series_cba.csv')
    parser.add_argument('--breakdown', type=str, help='Ruta a breakdown_<period>.csv')
    parser.add_argument('--output', type=str, help='Ruta de salida del HTML')
    args = parser.parse_args()

    period = args.period
    series_path = args.series
    breakdown_path = args.breakdown or f'exports/breakdown_{period}.csv'
    out_path = args.output or f'reports/{period}.html'

    render_report(out_path, period, series_path, breakdown_path)
    print(f"Reporte generado: {out_path}")
