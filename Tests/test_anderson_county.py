from Utils.tax_util import *
import json
from urllib.request import urlopen
from PIL import Image
import pytest


def test_get_gis_info_anderson():
    tm = '410502018'  # '690101037'
    params = {
        'f': 'json',
        'where': "TMS = '" + tm + "'",
        'outFields': '*'
    }
    url = 'https://propertyviewer.andersoncountysc.org/arcgis/rest/services/NewPropertyViewer/MapServer/5/query?'
    response = run_query(url, params)
    response_test = response.status_code == 200
    output = json.loads(response.text)
    attr = output['features'][0]['attributes']
    cols = ['SHAPE.STArea()', 'MRKT_VALUE', 'IMPRV']
    # Check if all required columns are found
    col_test = all(col in attr.keys() for col in cols)
    corner_test = len(output['features'][0]['geometry']['rings'][0]) > 0
    wkid_test = output['spatialReference']['latestWkid'] > 0

    # Uncomment this section if you need bbox updates for the next test
    # import pandas as pd
    # corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
    # bbox = box_maker(corners)
    # print(bbox)

    if response_test and col_test and corner_test and wkid_test:
        test = True
    else:
        test = False

    assert test


def test_get_gis_info_anderson2():
    tm = '690101037'
    tm2 = tm.rjust(11, '0') + '00000'
    params = {'mapno': tm2}
    url = 'https://acpass.andersoncountysc.org/asrdetails.cgs?'
    response = run_query(url, params)
    response_test = response.status_code == 200
    assert response_test


def test_find_lake_props_anderson():
    bbox = '1465567.7484762499%2C983512.2906746987%2C1466249.4010000774%2C984150.1135617774'
    url = ('https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Overlays/MapServer/export?dpi=96&'
           'transparent=true&format=png8&layers=show%3A1&bbox=')
    url = url + bbox
    url = url + '&bboxSR=102733&imageSR=102733&size=759%2C885&f=image'

    img = Image.open(urlopen(url))
    pixel_count = img.size[0] * img.size[1]
    img_list = list(img.getdata())
    # print(img.mode, img.size, img.info, img.getbands())
    # img2 = img.convert('RGB')
    # img2.show()
    # print([img_list.count(x) for x in range(max(img_list))])

    lake_pixel = 1
    lake_count = img_list.count(lake_pixel)
    lake_pct = (lake_count / pixel_count) * 100

    assert lake_pct == pytest.approx(23.3034, 0.0001)
