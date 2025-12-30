# Utilities

import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta


def get_counties():
    return ['greenville', 'anderson', 'spartanburg']


def get_cols():
    return ['item', 'taxmap', 'account', 'owner', 'address', 'subdiv', 'tax_dist', 'bldgs', 'acres', 'land_use',
            'bldg_type', 'bedrooms', 'sq_ft', 'dpsf', 'yr_built', 'appraised_land', 'appraised_bldg', 'appraised_total',
            'bldg_ratio', 'sale_price', 'sale_date', 'lake%', 'bbox', 'lat', 'long', 'dist1', 'dist2', 'dist3',
            'withdrawn', 'county_link', 'map_link', 'amount_due', 'comments', 'rating', 'bid', 'max_bid']


def get_type():
    type_dict = {
        'item': int,
        'taxmap': str,
        'account': str,
        'owner': str,
        'address': str,
        'subdiv': str,
        'tax_dist': str,
        'bldgs': float,
        'acres': float,
        'land_use': str,
        'bldg_type': str,
        'bedrooms': float,
        'sq_ft': float,
        'dpsf': float,
        'yr_built': str,
        'appraised_land': float,
        'appraised_bldg': float,
        'appraised_total': float,
        'bldg_ratio': float,
        'sale_price': float,
        'sale_date': str,
        'lake%': float,
        'bbox': str,
        'lat': float,
        'long': float,
        'dist1': str,
        'dist2': str,
        'dist3': str,
        'withdrawn': str,
        'county_link': str,
        'map_link': str,
        'amount_due': float,
        'comments': str,
        'rating': float,
        'bid': str,
        'est_bid': float,
        'max_bid': float,
    }
    return type_dict


def geo_convert(lat, lon, wkid):
    from pyproj import Transformer
    # EPSG:4326 is equivalent to WGS84 which gives standard lat/lon
    if wkid < 100000:
        transformer = Transformer.from_crs('EPSG:' + str(wkid), 'EPSG:4326')
    else:
        transformer = Transformer.from_crs('ESRI:' + str(wkid), 'EPSG:4326')

    return transformer.transform(lat, lon)


def meters_to_latlon(mx, my):
    # Not currently used
    import math
    "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"
    origin_shift = 2 * math.pi * 6378137 / 2.0
    lon = (mx / origin_shift) * 180.0
    lat = (my / origin_shift) * 180.0

    lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lon


def dpsf_calc(appraised_total, sq_ft):
    if sq_ft is not None and sq_ft > 0:
        return round(appraised_total / sq_ft, 0)
    else:
        return float('nan')


def from_excel_serial(ordinal: float, _epoch0=datetime(1899, 12, 31)):
    if ordinal >= 60:
        ordinal -= 1  # Excel leap year bug, 1900 is not a leap year!
    return (_epoch0 + timedelta(days=ordinal)).replace(microsecond=0).strftime('%m/%d/%Y')


def print_text2(obj1, inp):
    import tkinter as tk

    obj1['state'] = 'normal'
    obj1.insert(tk.END, str(inp) + '\n')
    obj1['state'] = 'disabled'
    obj1.see(tk.END)
    # obj1.update_idletasks()
    obj1.update()


def polygon_area(points):
    # Output is in acres
    area = 0  # Accumulates area
    j = len(points) - 1

    for i in range(len(points)):
        area += (points['x'].iloc[j] + points['x'].iloc[i]) * (points['y'].iloc[j] - points['y'].iloc[i])
        j = i  # j is the previous vertex to i

    return area / 2 / 43560


def box_maker(corners):
    # Takes corners from GIS and adds buffer to create a box for lake lookups
    margin = 250  # In meters, I'm 95% sure
    bbox = (str(corners['x'].min() - margin) + '%2C' +
            str(corners['y'].min() - margin) + '%2C' +
            str(corners['x'].max() + margin) + '%2C' +
            str(corners['y'].max() + margin))
    return bbox


def run_query(url, params, verify=False):
    # Not tested directly
    retries = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[408, 429, 500, 502, 503, 504],
    )
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session.get(url, params=params, verify=verify)


def merge_data():
    """
    This is a custom function to merge comments and rating generated in excel with the latest data from the tool

    Saving csv from excel kills some of the columns (County and Map links specifically, and possibly others if you
    don't select the option to not convert)

    """
    import pandas as pd
    filename1 = '../Counties/Greenville/props.csv'
    filename2 = '../Counties/Greenville/props3.csv'

    props_from_tool = pd.read_csv(filename1, sep=',', dtype=get_type())
    props_from_excel = pd.read_csv(filename2, sep=',', dtype=get_type())

    # col = ['comments', 'rating', 'est_bid', 'max_bid']
    col = ['comments', 'rating']

    # Set the key column as index for both dataframes
    props_from_tool.set_index('item', inplace=True)
    props_from_excel.set_index('item', inplace=True)

    # Overwrite the columns directly
    props_from_tool.update(props_from_excel[col])

    # Update function doesn't update if column doesn't exist
    # props_from_tool['est_bid'] = props_from_excel['est_bid']

    # Reset index if you want 'id' back as a column
    props_from_tool.reset_index(inplace=True)

    props_from_tool.to_csv(filename1, index=False, na_rep='NaN')


if __name__ == '__main__':
    merge_data()
