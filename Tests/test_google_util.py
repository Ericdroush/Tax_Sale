from Utils.google_util import run_google_api, reverse_geo, geocode, find_distance, get_streetview
import pytest


def test_run_google_api_geocode():
    params = {'address': '101 Main St Greer, SC'}
    assert run_google_api('geocode', params)['status'] == 'OK'


def test_run_google_api_distancematrix():

    origin = '101 Main St Greer SC'
    destinations = '101 Main St Greenville SC'

    params = {
        'origins': origin,
        'destinations': destinations,
        'units': 'imperial'
    }

    assert run_google_api('distancematrix', params)['status'] == 'OK'


def test_reverse_geo():
    lat, lon = 34.521489634608244, -82.62542004892643
    assert reverse_geo(lat, lon) == 'G9CF+HRW Anderson, SC, USA'


def test_geocode():
    assert geocode('G9CF+HRW Anderson, SC, USA')[0] == pytest.approx(34.521489634608244, 0.0001)


def test_find_distance_single():
    origin = '101 Main St Greer SC'
    destinations = ['101 Main St Greenville SC']
    assert find_distance(origin, destinations) == pytest.approx([17.3, 'NaN', 'NaN'], abs=3)


def test_find_distance_multi():
    origin = '101 Main St Greer SC'
    destinations = ['101 Main St Greenville SC', '101 Main St Simpsonville, SC', '101 Main St Mauldin SC']
    assert find_distance(origin, destinations) == pytest.approx([16.9, 15.8, 16.1], abs=3)


def test_find_distance_failed():
    origin = '101 Main St Greer SC'
    destinations = ['The moon']
    assert find_distance(origin, destinations) == ['Failed', 'NaN', 'NaN']
