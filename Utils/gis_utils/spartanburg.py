# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 19:44:27 2022

Steps:
    Need to get the newspaper add and save as a CSV

@author: ericd
"""

from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import sys
import time
from datetime import date
import numpy as np

# adding utils to the system path
sys.path.insert(0, 'C:/Users/ericd/OneDrive/Documents/Python Scripts/Tax_Sale/Utils')
from tax_util import *
from google_util import *


def obtain_props(pwin):

    # Prep work
    # Go to this website https://www.spartanburgcounty.org/640/2023-Tax-Sale-Info
    # Click on Real Estate
    # On the new webpage press Ctrl+A to select all and Ctrl+C to copy
    # Paste in a text file called props_from_web.csv in this directory
    #   C:\Users\ericd\OneDrive\Documents\Python Scripts\Tax_Sale\Counties\Spartangburg

    print_text(pwin, 'Retrieving tax sale properties ...')

    filename = 'Counties/Spartanburg/props_from_web.csv'
    with open(filename) as f:
        props = f.readlines()

    props[0] = 'item,taxmap,description\n'  # Set the header

    for i in range(1, len(props)):
        props[i] = props[i].replace(',', '')
        if props[i][0:4].isnumeric():
            props[i] = props[i].replace(' ', ',', 2)  # Adds a comma after the first space
        else:
            # Removes the carriage return from the previous line, lines will get combined at export
            props[i - 1] = props[i - 1].rstrip()

    filename = 'Counties/Spartanburg/props_clean_from_web.csv'
    out = open(filename, 'w')
    for line in props:
        out.write(line)
    out.close()

    props = pd.read_csv(filename, sep=',', dtype=str)

    print_text(pwin, str(len(props)) + ' tax sale properties has been retrieved...')

    return props


def get_gis_info(pwin, filename):
    import json

    # Pull list of properties from website
    props = obtain_props(pwin).head(5)  # Can limit # of properties here for testing, just append .head(5)
    total_count = len(props)

    cols = get_cols()
    props_new = pd.DataFrame(columns=cols)

    if Path(filename).is_file():
        props_old = pd.read_csv(filename, sep=',', dtype=get_type())
    else:
        props_new.to_csv(filename, index=False)  # Write out headers
        props_old = pd.DataFrame(columns=['taxmap'])  # Creates empty dataframe to compare to, won't find anything and will write out all taxmaps

    prop_count = 0
    t0 = time.perf_counter()
    dt = []
    for prop in props.index:

        tm = props['taxmap'].iloc[prop]
        if not (props_old['taxmap'].eq(tm)).any():

            if len(str(tm)) > 5:  # Check for valid TaxMap ID
                #print(tm)

                # Query property details
                #tm = '7-11-07-067.00'
                params = {
                    'f': 'json',
                    'where': "MAPNUMBER = '" + tm + "'",
                    'outFields': '*'
                }

                url = 'https://maps.spartanburgcounty.org/server/rest/services/OneMap/Tax_Parcels/MapServer/1/query?'
                response = run_query(url, params)

                output = json.loads(response.text)
                # Acreage
                # City
                # DEEDACREAGE
                # DeedBook
                # DeedPage
                # District
                # InstrumentNumber
                # LegalDescription
                # LotNumber
                # MAPNUMBER
                # MiscTxt
                # OBJECTID
                # OwnerName
                # PARCELNUMBER
                # PreviousOwnerName
                # SUBDIVISION
                # SaleAmount
                # SaleDate
                # State
                # StreetAddress
                # TAXPIN
                # TaxpayerName
                # YearBuilt
                # Zip
                # print(output['features'][0]['attributes']['PIN'])
                # print(output['features'][0]['attributes'].items())
                # print(output['features'][0]['geometry']['rings'][0])

                if len(output['features']) == 0:  # Didn't get something back from the website
                    props_new.loc[0] = 'NaN'  # Fill with NaN
                    props_new['taxmap'].loc[0] = tm
                    props_new['item'].loc[0] = props['item'].iloc[prop]
                    props_new['owner'].loc[0] = props['owner'].iloc[prop]

                    # props_new['account'].loc[0] = 'County query failed'
                    # props_new['owner'].loc[0] = url
                    props_new.to_csv(filename, mode='a', index=False, header=False)

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
                    item = props['item'].iloc[prop]
                    account = 'NaN'
                    owner = attr['OwnerName']
                    subdiv = attr['SUBDIVISION']
                    tax_dist = attr['District']
                    landuse = 'NaN'
                    bldg_type = 'NaN'
                    bedrooms = 'NaN'
                    sq_ft = 'NaN'
                    appraised_total = 'NaN'
                    #sale_price = attr['SALE_PRICE']
                    sale_date = from_excel_serial(attr['SaleDate'] / 86400 / 1000 + 25569)
                    bldgs = 'NaN'
                    yr_built = attr['YearBuilt']

                    # Calculated parameters
                    #dpsf =  dpsf_calc(appraised_total, sq_ft)
                    dpsf = 'NaN'  #Hard code to NaN since sq_ft not available for this county

                    corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
                    acres = polygon_area(corners)

                    wkid = output['spatialReference']['latestWkid']
                    lat, lon = geo_convert(corners['x'].mean(), corners['y'].mean(), wkid)

                    address = reversegeo(lat, lon)

                    bbox = str(corners['x'].min()) + '%2C' + str(corners['y'].min())  + '%2C' + str(corners['x'].max())  + '%2C' + str(corners['y'].max())
                    withdrawn = 'A'

                    #Call second website for additional details
                    params = {
                        'AppID': '857',
                        'LayerID': '16069',
                        'PageTypeID': '4',
                        'PageID': '7149',
                        'Q': '692867197',
                        'KeyValue': tm

                    }
                    url = 'https://qpublic.schneidercorp.com/Application.aspx?'
                    response = run_query(url, param)

                    soup = BeautifulSoup(response.content, 'html.parser')


                    sp1 = 0
                    sp2 = 0
                    for a in soup.find_all('td', text='Date'):
                        b = a.parent.find_next('tr').get_text()
                        if b.count('\n') > 4:  # This line has sales dat
                            sd1 = b.split('\n')[1]
                            c = b.split('\n')[4].replace('$', '').replace(',', '').strip()
                            if len(c) > 0:
                                sp1 = float(c)
                            else:
                                sp1 = 0
                            if sp1 < 11:  # Screen for junk sales
                                b = a.parent.find_next('tr').find_next('tr').get_text()
                                if b.count('\n') > 4:  # This line has sales dat
                                    sd2 = b.split('\n')[1]
                                    c = b.split('\n')[4].replace('$', '').replace(',', '').strip()
                                    if len(c) > 0:
                                        sp2 = float(c)
                                    else:
                                        sp2 = 0

                    if sp1 == 0 and sp2 == 0:
                        sale_price = 'NaN'
                        sale_date = 'NaN'
                    elif sp1 >= sp2:
                        sale_price = sp1
                        sale_date = sd1
                    else:
                        sale_price = sp2
                        sale_date = sd2

                    # Could get subdivision here if needed
                    for a in soup.find_all('div', text=str(date.today().year)):
                        b = a.parent.parent.get_text()  # Year, Acre, lots, Land Asmt, #Bldg, Bldg Asmt, Tot Asmt, Rat CD, RC
                        if b.count('\n') > 4:
                            if len(b.split('\n')[4].strip()) > 0:
                                appraised_land = b.split('\n')[4].strip()
                            else:
                                appraised_land = 'NaN'
                            if len(b.split('\n')[6].strip()) > 0:
                                appraised_bldg = b.split('\n')[6].strip()
                            else:
                                appraised_bldg = 'NaN'
                            if len(b.split('\n')[7].strip()) > 0:
                                asmt_total = b.split('\n')[7].strip()
                            else:
                                asmt_total = 'NaN'
                            if appraised_land == 'NaN' or asmt_total == 'NaN':
                               bldg_ratio = 'NaN'
                            else:
                                bldg_ratio = (1 - round(int(appraised_land)/int(asmt_total),2)) * 100

                    county_link = '=HYPERLINK("https://propertyviewer.andersoncountysc.org/mapsjs/?TMS=' + tm + '&disclaimer=false","County")'
                    map_link = '=HYPERLINK("http://maps.google.com/maps?t=k&q=loc:' + str(lat) + '+' + str(lon) + '","Map")'
                    #map_link = 'http://maps.google.com/maps?t=k&q=loc:' + str(lat) + '+' + str(lon)

                    #            'item',             'taxmap', 'account', 'owner',                    'address', 'subdiv', 'tax_dist',
                    #            'bldgs', 'acres', 'land_use','bldg_type', 'bedrooms', 'sq_ft', 'dpsf', 'yr_built','appraised_land', 'appraised_bldg', 'appraised_total',
                    #             'bldg_ratio', 'sale_price', 'sale_date', 'lake%', 'bbox', 'lat', 'lon', 'dist1', 'dist2', 'dist3', 'withdrawn', 'county_link', 'map_link',
                    #            'amount_due', 'comments', 'rating', 'bid'
                    data_list = [item, tm, account, owner, address, subdiv, tax_dist,
                             bldgs, acres, landuse, bldg_type, bedrooms, sq_ft, dpsf, yr_built, appraised_land, appraised_bldg, appraised_total,
                             bldg_ratio, sale_price, sale_date, 'NaN', bbox, lat, lon, 'NaN', 'NaN', 'NaN', withdrawn, county_link, map_link,
                             float(props['amount_due'].iloc[prop].strip('$').replace(',','')), '', '', '']

                    props_new.loc[0] = data_list
                    props_new.to_csv(filename, mode='a', index=False, header=False)
        else:  # if tm is already found... occurs when you need to restart
            prop_count += 1

    return prop_count


def update_withdrawn(pwin, filename):

    # Pull list of properties from website
    props = obtain_props(pwin)  # Limit to 3 properties for testing

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

    if Path(filename).is_file():
        props = pd.read_csv(filename, sep=',', dtype=get_type())

        for index, row in props.iterrows():
            if pd.isna(row['bbox']):
                row['lake%'] = 'NaN'
            else:
                url = 'https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Overlays/MapServer/export?dpi=96&transparent=true&format=png8&layers=show%3A1&bbox='
                url = url + row['bbox']
                url = url + '&bboxSR=102733&imageSR=102733&size=759%2C885&f=image'

                img = Image.open(urlopen(url))
                pixel_count = img.size[0] * img.size[1]
                img_list = list(img.getdata())
                # These statements can help dig into the details of the image to figure out how lakes are ID'd
                #print(img.mode, img.size, img.info, img.getbands())
                #img2 = img.convert('RGB')
                #img.show()
                #print([img_list.count(x) for x in range(max(img_list))])

                lake_pixel = 1
                lake_count = img_list.count(lake_pixel)
                lake_pct = (lake_count / pixel_count) * 100

                row['lake%'] = lake_pct

        props.to_csv(filename, index=False, na_rep='NaN')

        return True

    else:
        print_text(pwin, "Properties haven't been found yet, need to do that before finding lake properties")
        return False



