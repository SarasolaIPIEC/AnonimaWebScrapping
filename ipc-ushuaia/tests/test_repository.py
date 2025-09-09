"""
Tests para acceso y guardado de datos históricos.
"""
import pandas as pd
import tempfile
import os
from src import repository

def test_save_and_load_csv():
    df = pd.DataFrame({'index': [100, 110]}, index=['2024-01', '2024-02'])
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        repository.save_historical_data(df, csv_path=tmp.name)
        df2 = repository.load_historical_data(csv_path=tmp.name)
        assert df2.shape == df.shape
    os.unlink(tmp.name)
