import os
from pathlib import Path

from src.reporting.render import render_report


def test_render_basic(tmp_path: Path):
    exports = tmp_path / 'exports'
    reports = tmp_path / 'reports'
    exports.mkdir()
    reports.mkdir()
    period = '2025-01'

    # minimal series (single point → no chart)
    (exports / 'series_cba.csv').write_text(
        'period,cba_ae,cba_family,idx,mom,yoy\n' +
        f'{period},100.00,309.00,100.00,,\n',
        encoding='utf-8'
    )
    # minimal breakdown (one row)
    (exports / f'breakdown_{period}.csv').write_text(
        'period,item_id,name,query,title,url,brand_tier,cba_flag,category,in_stock,promo_flag,price_original,price_promo,price_final,unit_price_base,qty_base,expected_qty,cost_item_ae,substitution\n'
        f'{period},yerba_1kg,Yerba 1 kg,,Yerba 1 kg,,standard,si,almacen,1,0,,,$ 1000,1000,1.0,0.75,750,\n',
        encoding='utf-8'
    )

    out = reports / f'{period}.html'
    render_report(str(out), period, str(exports / 'series_cba.csv'), str(exports / f'breakdown_{period}.csv'))
    html = out.read_text(encoding='utf-8')
    assert 'Aún no hay serie histórica' in html
    assert 'aria-sort' in html
    assert 'CBA AE' in html
