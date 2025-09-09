"""
Tests para generación de reportes automáticos.
"""
import pandas as pd
from src import report

def test_generate_summary_report():
    df = pd.DataFrame({'index': [100, 110, 120]})
    resumen = report.generate_summary_report(df)
    assert 'media=110.00' in resumen
    assert 'última=120.00' in resumen
