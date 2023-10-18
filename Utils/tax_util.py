# Utilities


def get_cols():
    return ['item', 'taxmap', 'account', 'owner', 'address', 'subdiv', 'tax_dist', 'bldgs', 'acres', 'land_use',
            'bldg_type', 'bedrooms', 'sq_ft', 'dpsf', 'yr_built', 'appraised_land', 'appraised_bldg', 'appraised_total',
            'bldg_ratio', 'sale_price', 'sale_date', 'lake%', 'bbox', 'lat', 'long', 'dist1', 'dist2', 'dist3', 'withdrawn', 'county_link', 'map_link',
            'amount_due', 'comments', 'rating', 'bid']

def get_type():
    type_dict = {
        'item': int,
        'taxmap': str,
        'account': str,
        'owner': str,
        'address': str,
        'subdiv': str,
        'tax_dist': float,
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
        'bid': float
    }
    return type_dict

def geo_convert(lat, lon, wkid):
    from pyproj import Transformer
    #EPSG:4326 is equivalent to WGS84 which gives standard lat/lon
    if wkid < 100000:
        transformer = Transformer.from_crs('EPSG:' + str(wkid), 'EPSG:4326')
    else:
        transformer = Transformer.from_crs('ESRI:' + str(wkid), 'EPSG:4326')

    return transformer.transform(lat,lon)


def MetersToLatLon(mx, my):
    import math
    "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"
    originShift = 2 * math.pi * 6378137 / 2.0
    lon = (mx / originShift) * 180.0
    lat = (my / originShift) * 180.0

    lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lon

def dpsf_calc(appraised_total, sq_ft):
    if sq_ft is not None and sq_ft > 0:
        return round(appraised_total / sq_ft, 0)
    else:
        return float('nan')

from datetime import datetime, timedelta
def from_excel_serial(ordinal: float, _epoch0=datetime(1899, 12, 31)) -> datetime:
    if ordinal >= 60:
        ordinal -= 1  # Excel leap year bug, 1900 is not a leap year!
    return (_epoch0 + timedelta(days=ordinal)).replace(microsecond=0).strftime('%m/%d/%Y')

def print_text(obj1, inp):
    import tkinter as tk

    obj1['state'] = 'normal'
    obj1.insert(tk.END, str(inp) + '\n')
    obj1['state'] = 'disabled'
    obj1.see(tk.END)
    obj1.update_idletasks()
