from Utils.tax_util import *
import pytest
import pandas as pd


def test_get_cols():
    assert len(get_cols()) == len(get_type())


def test_get_type():
    assert len(get_type()) == len(get_cols())


def test_geo_convert():
    lat = 1510430.8127932462
    lon = 981911.2924082115
    wkid = 102733
    assert geo_convert(lat, lon, wkid) == (34.521489634608244, -82.62542004892643)


def test_dpsf_calc_normal():
    appraised_total, sq_ft = 200000, 1000
    assert dpsf_calc(appraised_total, sq_ft) == 200

@pytest.mark.parametrize(('appraised_total', 'sq_ft'), [(2000000, None), (2000000, 0)])
def test_dpsf_calc_nan(appraised_total, sq_ft):
    assert dpsf_calc(appraised_total, sq_ft) == pytest.approx(float('nan'), nan_ok=True)


def test_from_excel_serial():
    assert from_excel_serial(50000) == '11/21/2036'


def test_polygon_area_square():
    points = pd.DataFrame(data=[(0, 0), (0, 1), (1, 1), (1, 0)], columns=['x', 'y'])
    assert polygon_area(points) == 1 / 43560


def test_polygon_area_tri():
    points = pd.DataFrame(data=[(0, 0), (0, 1), (1, 0.5)], columns=['x', 'y'])
    assert polygon_area(points) == 1 / 2 / 43560


def test_polygon_area_rect():
    points = pd.DataFrame(data=[(0, 0), (0, 2), (1, 2), (1, 0)], columns=['x', 'y'])
    assert polygon_area(points) == 2 / 43560


def test_box_maker():
    points = pd.DataFrame(data=[(1000, 1000), (2000, 1000), (2000, 2000), (1000, 2000)], columns=['x', 'y'])
    assert box_maker(points) == '750%2C750%2C2250%2C2250'
