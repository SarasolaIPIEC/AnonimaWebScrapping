"""
Tests para funciones de exportación a CSV, JSON y HTML.
"""
import pandas as pd
import os
from src import exporter

def test_export_to_csv(tmp_path):
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    out = tmp_path / 'test.csv'
    exporter.export_to_csv(df, str(out))
    assert out.exists()
    df2 = pd.read_csv(out)
    assert df2.shape == (2, 2)

def test_export_to_json(tmp_path):
    df = pd.DataFrame({'a': [1], 'b': [2]})
    out = tmp_path / 'test.json'
    exporter.export_to_json(df, str(out))
    assert out.exists()

def test_export_to_html(tmp_path):
    df = pd.DataFrame({'a': [1], 'b': [2]})
    out = tmp_path / 'test.html'
    exporter.export_to_html(df, str(out))
    assert out.exists()
