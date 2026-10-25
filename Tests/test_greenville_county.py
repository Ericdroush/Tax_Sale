from Utils.tax_util import *
import json
from urllib.request import urlopen
from PIL import Image
import pytest
import requests
from requests.exceptions import ConnectionError


def test_import_props_greenville():
    req = requests.get('https://www.greenvillecounty.org/appsAS400/Taxsale/')
    assert req.status_code == 200


def test_get_gis_info_greenville():
    tm = '0554020100106'  # Test property
    params = {
        'f': 'json',
        'geometryPrecision': 0,
        'maxAllowableOffset': 4,
        'resultOffset': 0,
        'resultRecordCount': 1000,
        'orderByFields': 'OWNAM1',
        'outSR': '{"wkid":103146,"vcsWkid":105703}',
        'spatialRel': 'esriSpatialRelIntersects',
        'where': "PIN = '" + tm + "'",   # pin%20%3D%20%270512010101102%27
        'outFields': '*'
    }

    url = 'https://www.gcgis.org/arcgis3/rest/services/GreenvilleNJ/Tax_Parcel_Search_and_Select/MapServer/0/query?'
    response = run_query(url, params)
    response_test = response.status_code == 200
    output = json.loads(response.text)
    print(json.dumps(output, indent=2))
    attr = output['features'][0]['attributes']
    cols = ['SUBDIV', 'DIST', 'TACRES', 'LANDUSE', 'BEDROOMS', 'SQFEET', 'FAIRMKTVAL', 'SLPRICE',
            'DEEDDATE', 'POWNNM']
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


def test_find_lake_props_greenville():
    # Original Test bbox
    bbox = '1646762.2575459331%2C1067619.7086614221%2C1648818.8061023653%2C1069904.5104986876'
    # url = ('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96'
    #        '&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=')

    # Lots of layers
    # url = ('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96'
    #        '&transparent=true&format=png8&layers=show%3A52%2C39%2C40%2C77%2C48%2C47%2C50%2C38%2C35%2C41%2C43%2C16%2C17&bbox=')

    # No water
    # bbox = '1636662.59973754%2C1088070.4514435679%2C1637408.177821517%2C1088863.8562992066'

    # Some water
    bbox = '1639164.0964566916%2C1094347.9937663972%2C1640217.7037401646%2C1095424.4917978942'
    # Water layers in the Greenville_Base service: 5 = Stream, 6 = Lake or River
    # (the old GreenvilleJS/Map_Layers_JS service no longer exists)
    url = ('https://www.gcgis.org/arcgis3/rest/services/GCGIA/Greenville_Base/MapServer/export?dpi=96'
           '&transparent=true&format=png8&layers=show%3A5%2C6&bbox=')
    url = url + bbox
    url = url + '&bboxSR=6570&imageSR=6570&size=937%2C955&f=image'

    img = Image.open(urlopen(url)).convert('RGBA')
    pixel_count = img.size[0] * img.size[1]

    # Transparent pixels (alpha == 0) are background; anything else is water
    water_count = sum(1 for px in img.getdata() if px[3] > 0)
    lake_pct = water_count / pixel_count * 100

    assert lake_pct == pytest.approx(8.8, rel=0.02)
