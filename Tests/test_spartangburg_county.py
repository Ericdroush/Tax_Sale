from Utils.tax_util import *
import json
from urllib.request import urlopen
from PIL import Image
import pytest


def test_get_gis_info_spartanburg():
    tm = '7-11-07-067.00'
    params = {
        'f': 'json',
        'where': "MAPNUMBER = '" + tm + "'",
        'outFields': '*'
    }
    url = 'https://maps.spartanburgcounty.org/server/rest/services/OneMap/Tax_Parcels/MapServer/1/query?'
    response = run_query(url, params)
    response_test = response.status_code == 200
    output = json.loads(response.text)
    attr = output['features'][0]['attributes']
    cols = ['OwnerName', 'SUBDIVISION', 'District', 'YearBuilt']
    # Check if all required columns are found
    col_test = all(col in attr.keys() for col in cols)
    corner_test = len(output['features'][0]['geometry']['rings'][0]) > 0
    wkid_test = output['spatialReference']['latestWkid'] > 0

    # Uncomment this section if you need bbox updates for the next test
    import pandas as pd
    corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
    bbox = box_maker(corners)
    print(bbox)

    if response_test and col_test and corner_test and wkid_test:
        test = True
    else:
        test = False

    assert test


def test_get_gis_info_spartanburg2():
    # Not sure if I want to create all the Chrome driver logic here
    assert True


def test_find_lake_props_anderson():
    # Logic doesn't exist for Spartanburg
    assert True
