# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 19:44:27 2022

@author: ericd
"""

import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import sys
import time

# adding utils to the system path
sys.path.insert(0, 'C:/Users/ericd/OneDrive/Documents/Python Scripts/Tax_Sale/Utils')
from tax_util import *
from google_util import *

def obtain_props(pwin):
    import io

    print_text(pwin, 'Retrieving tax sale properties ...')

    req = requests.get('http://www.greenvillecounty.org/appsAS400/Taxsale/')
    soup = BeautifulSoup(req.content, 'html.parser')

    a = soup.find_all('table')
    props = pd.read_html(io.StringIO(str(a)))[0]   #Item #, Map #, Name, Amount Due
    props.columns = ['item', 'taxmap', 'owner', 'amount_due']  # Translate into standard names

    print_text(pwin, str(len(props)) + ' tax sale properties has been retrieved...')

    return props


def get_gis_info(pwin, filename):
    import json

    # Pull list of properties from website
    props = obtain_props(pwin)  #.head(5) Limit to 5 properties for testing
    total_count = len(props)

    cols = get_cols()
    props_new = pd.DataFrame(columns=cols)

    if Path(filename).is_file():
        props_old = pd.read_csv(filename, sep=',', dtype=get_type())
    else:
        props_new.to_csv(filename, index=False)  # Write out headers
        props_old = pd.DataFrame(columns=['taxmap'])  # Creates empty dataframe to compare to, won't find anything and will write out all taxmaps

    prop_count = 0
    t0 = t1 = time.perf_counter()
    dt = []
    for prop in props.index:

        tm = props['taxmap'].iloc[prop]
        if not (props_old['taxmap'].eq(tm)).any():

            if len(str(tm)) > 5:  # Check for valid TaxMap ID
                #print(tm)

                # Query property details
                #tm = '0687080101100'
                params = {
                    'f': 'json',
                    'where': "PIN = '" + tm + "'",
                    'outFields': '*'
                }
                # url = 'https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/53/query?f=json&where=PIN%20%3D%20%27'
                # url = url + tm + '%27&returnGeometry=true&spatialRel=esriSpatialRelIntersects&maxAllowableOffset=4&geometryPrecision=0&outFields=*&outSR=6570'

                url = 'https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/53/query?'

                response = run_query(url, params)
                output = json.loads(response.text)

                # "PIN": "PIN / Tax Map #",
                # "OWNAM1": "Owner Name(MixedCase)",
                # "OWNAM2": "Owner Name 2(MixedCase)",
                # "STREET": "Mailing Address(MixedCase)",
                # "CITY": "City(MixedCase)",
                # "STATE": "State",
                # "ZIP5": "Zip Code",
                # "NAMECO": "In Care Of(MixedCase)",
                # "POWNNM": "Previous Owner(MixedCase)",
                # "DEEDDATE": "Deed Date(ShortDate)",
                # "CUBOOK": "Deed Book",
                # "CUPAGE": "Deed Page",
                # "PLTBK1": "Plat Book",
                # "PPAGE1": "Plat Page",
                # "DIST": "Tax District",
                # "MKTAREA": "Market Area",
                # "JURIS": "Jurisdiction",
                # "LANDUSE": "Land Use",
                # "DESCR": "Legal Description",
                # "SUBDIV": "Subdivision(MixedCase)",
                # "STRNUM": "Site Address Number",
                # "LOCATE": "Site Address Street",
                # "SLPRICE": "Sale Price(Money)",
                # "FAIRMKTVAL": "Fair Market Value(Money)",
                # "TAXMKTVAL": "Taxable Market Value(Money)",
                # "TOTTAX": "Taxes(Money)",
                # "PAIDDATE": "Date Taxes Paid(ShortDate)",
                # "TACRES": "Estimated Acres",
                # "SQFEET": "Square Feet",
                # "BEDROOMS": "Number of Bedrooms",
                # "BATHRMS": "Number of Bathrooms",
                # "HALFBATH": "Number of Half Baths",
                # "PROPTYPE": "99! PROPTYPE",
                # "IMPROVED": "99! IMPROVED",
                # "OBJECTID": "OBJECTID"
                # print(output['features'][0]['attributes']['PIN'])
                # print(output['features'][0]['attributes'].items())
                # print(output['features'][0]['geometry']['rings'][0])

                if len(output['features']) == 0:  # Didn't get something back from the website
                    pass
                    # props_new.loc[0] = 'NaN'  # Fill with NaN
                    # props_new['item'].loc[0] = props['item'].iloc[prop]
                    # props_new['taxmap'].loc[0] = tm
                    # props_new.to_csv(filename, mode='a', index=False, header=False)

                else:
                    prop_count += 1
                    t1 = time.perf_counter()
                    dt.append(t1 - t0)
                    t0 = t1
                    est_time_left = round(sum(dt)/len(dt) * (total_count - prop_count),0)
                    print_text(pwin, '{0}/{1}  Tax map ID: {2} Estimated time remaining = {3}s'.format(str(prop_count),
                                                                                                       str(total_count),
                                                                                                       str(tm),
                                                                                                       str(est_time_left)))
                    attr = output['features'][0]['attributes']
                    # print(attr)
                    # Direct read parameters
                    #address = attr['STREET'] + attr['CITY'] + ', ' + attr['STATE'] #Not reliable
                    account = 'NaN'
                    subdiv = attr['SUBDIV']
                    tax_dist = attr['DIST']
                    # if attr['IMPROVED'] == 'no':
                    #     bldgs = 0
                    # else:
                    #     bldgs = 1
                    acres = attr['TACRES']
                    landuse = attr['LANDUSE']
                    if landuse == 1180 or landuse == 9171 or landuse == 6800:  #This doesn't work, always goes to 1, maybe landuse is a text?
                        bldgs = 0
                    else:
                        bldgs = 1
                    # 1100 Residential Single Family
                    # 1101 Residential Single Family with Auxiliary Use
                    # 1170 Residential Mobile Home with Land
                    # 1171 Residential Mobile Home on Mobile Home File
                    # 1180 Residential Vacant
                    # 1181 Homeowners Association Property
                    # 1182 Common Area
                    # 6800 Commercial Vacant
                    # 9170 Agricultural Vacant
                    # 9171 Agricultural Improved
                    bldg_type = attr['PROPTYPE']
                    bedrooms = attr['BEDROOMS']
                    sq_ft = attr['SQFEET']
                    appraised_total = attr['FAIRMKTVAL']
                    sale_price = attr['SLPRICE']
                    sale_date = from_excel_serial(attr['DEEDDATE'] / 86400 / 1000 + 25569)

                    # Calculated parameters
                    dpsf = dpsf_calc(appraised_total, sq_ft)

                    corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
                    if acres < 0.1:   # Only overwrite if acres wasn't defined
                        acres = polygon_area(corners)

                    wkid = output['spatialReference']['latestWkid']

                    lat, lon = geo_convert(corners['x'].mean(), corners['y'].mean(), wkid)

                    address = reversegeo(lat, lon)

                    bbox = str(corners['x'].min()) + '%2C' + str(corners['y'].min())  + '%2C' + str(corners['x'].max())  + '%2C' + str(corners['y'].max())
                    withdrawn = 'A'

                    county_link = '=HYPERLINK("https://www.gcgis.org/apps/GreenvilleJS/?PIN=' + tm + '","County")'
                    map_link = '=HYPERLINK("http://maps.google.com/maps?t=k&q=loc:' + str(lat) + '+' + str(lon) + '","Map")'

                    #            'item',             'taxmap', 'account', 'owner',                    'address', 'subdiv', 'tax_dist',
                    #            'bldgs', 'acres', 'land_use','bldg_type', 'bedrooms', 'sq_ft', 'dpsf', 'yr_built','appraised_land', 'appraised_bldg', 'appraised_total',
                    #             'bldg_ratio', 'sale_price', 'sale_date', 'lake%', 'bbox', 'lat', 'lon', 'dist1', 'dist2', 'dist3', 'withdrawn', 'county_link', 'map_link',
                    #            'amount_due', 'comments', 'rating', 'bid'
                    data_list = [props['item'].iloc[prop], tm, account, props['owner'].iloc[prop], address, subdiv, tax_dist,
                             bldgs, acres, landuse, bldg_type, bedrooms, sq_ft, dpsf, 'NaN', 'NaN', 'NaN', appraised_total,
                             'NaN', sale_price, sale_date, 'NaN', bbox, lat, lon, 'NaN', 'NaN', 'NaN', withdrawn, county_link, map_link,
                             float(props['amount_due'].iloc[prop].strip('$').replace(',','')), '', '', '']

                    props_new.loc[0] = data_list
                    props_new.to_csv(filename, mode='a', index=False, header=False)
        else:  # if tm is already found... occurs when you need to restart
            prop_count += 1

    return prop_count


def update_withdrawn(pwin, filename):

    # Pull list of properties from website
    props = obtain_props(pwin)  #.head(3) Limit to 3 properties for testing

    if Path(filename).is_file():
        props_main = pd.read_csv(filename, sep=',', dtype=get_type())
        initial_count = props_main['withdrawn'].value_counts()['A']
        props_main['withdrawn'] = 'W'   # Set all to withdrawn
        props['withdrawn'] = 'A'   # Set all remaining properties to available
        props_main['withdrawn'].update(props['withdrawn'])
        new_count = props_main['withdrawn'].value_counts()['A']
        withdrawn_count = initial_count - new_count

        props_main.to_csv(filename, index=False, na_rep='NaN')

    else:
        withdrawn_count = 0
        new_count = 0
        print_text(pwin, 'Opps!  You need to read properties first!')

    return new_count, withdrawn_count

def find_lake_props(pwin, filename):
    from urllib.request import urlopen
    from PIL import Image

    #layers=show%3A53%2C49%2C48
    #bbox = xmin, ymin, xmax, ymax - use min 1000m measurements
    #   Corner format saved during get_gis_info routine - may not be the same for each county...
    #url = []
    #Lots of lake - some layers 19%
    #url.append('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=1607371.9373959857%2C1154026.867110622%2C1608673.3288876575%2C1155353.258652294&bboxSR=6570&imageSR=6570&size=937%2C955&f=image')
    #No lake - 0%
    #url.append('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=1583956.6127875582%2C1147246.2979939282%2C1585258.0042792303%2C1148572.6895356001&bboxSR=6570&imageSR=6570&size=937%2C955&f=image')
    #Some river/pond - 8e-3%
    #url.append('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=1581395.4965542147%2C1144553.2370522511%2C1583998.2795375583%2C1147206.020135595&bboxSR=6570&imageSR=6570&size=937%2C955&f=image')
    #Pond - zoomed way in
    #url.append('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=1583171.9172041721%2C1145797.2437544896%2C1583562.334651674%2C1146195.1612169913&bboxSR=6570&imageSR=6570&size=937%2C955&f=image')
    #Whole lotta lake
    #url.append('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=1606007.8196930396%2C1154703.6514629384%2C1609911.9941680552%2C1158682.8260879542&bboxSR=6570&imageSR=6570&size=937%2C955&f=image')
    #Eric's hand built test
    #url.append('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=1607391%2C1154442%2C1608391%2C1155442&bboxSR=6570&imageSR=6570&size=937%2C955&f=image')


    if Path(filename).is_file():
        props = pd.read_csv(filename, sep=',', dtype=get_type())

        for index, row in props.iterrows():
            if row['bbox'] == 'NaN':
                row['lake%'] = 'NaN'
            else:
                url = 'https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox='
                url = url + row['bbox']
                url = url + '&bboxSR=6570&imageSR=6570&size=937%2C955&f=image'

                img = Image.open(urlopen(url))
                pixel_count = img.size[0] * img.size[1]
                img_list = list(img.getdata())
                # These statements can help dig into the details of the image to figure out how lakes are ID'd
                #print(img.mode, img.size, img.info, img.getbands())
                #img2 = img.convert('RGB')
                #img.show()
                #print([img_list.count(x) for x in range(max(img_list))])

                lake_pixel = 0
                lake_count = img_list.count(lake_pixel)
                lake_pct = (1 - lake_count / pixel_count) * 100

                row['lake%'] = lake_pct

        props.to_csv(filename, index=False, na_rep='NaN')

        return True

    else:
        print_text(pwin, "Properties haven't been found yet, need to do that before finding lake properties")
        return False



