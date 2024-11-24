# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 19:44:27 2022

Steps:
    Need to get the newspaper add and save as a CSV

Open Issues:
    Second site list "condition" - not sure how accurate or what to do with it
    I don't know where to get the amount due, but that's a big hole in this process
    Can't figure out how to create link to Spartanburg OneMap GIS
        https://maps.spartanburgcounty.org/portal/apps/webappviewer/index.html?id=8a88ed02adb845938c81f8c0c4214b9e&fbclid=IwAR3OKvDcpr8nzClR45GwrGJOmsErJTz3P-nr9dwwLnxT-VAKIsViiio33fM
    It appears I can get a reliable address from the second site but needs investigating to see how reliable it is - currently storing as account

@author: ericd
"""

from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import sys
import time
from datetime import date

# For Selenium calls
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math
from Utils.tax_util import *
from Utils.google_util import *


# adding utils to the system path
# sys.path.insert(0, 'C:/Users/ericd/OneDrive/Documents/Python Scripts/Tax_Sale/Utils')

def pull_data(driver, xpath):
    try:
        out = driver.find_element(By.XPATH, xpath).get_attribute(
            "textContent").replace('$', '').replace(',', '').strip()
    except:
        out = 'NaN'

    return out


def obtain_props(pwin):

    # Prep work
    # Go to this website https://www.spartanburgcounty.org/640/2023-Tax-Sale-Info
    # Click on Real Estate
    # On the new webpage press Ctrl+A to select all and Ctrl+C to copy
    # Paste in a text file called props_from_web.csv in this directory
    #   C:\Users\ericd\OneDrive\Documents\Python Scripts\Tax_Sale\Counties\Spartanburg

    print_text(pwin, 'Retrieving tax sale properties ...')

    filename = 'Counties/Spartanburg/props_from_web.csv'
    from glob import glob
    import os
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


def get_gis_info(pwin, filename, test_flag):
    import json

    # Selenium Setup
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Set the Chrome webdriver to run in headless mode for scalability
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    # Pass the defined options objects to initialize the web driver
    driver = Chrome(options=options)
    # Set an implicit wait of 5 seconds to allow time for elements to appear before throwing an exception - waits up to 5 seconds, not a min wait time like sleep
    driver.implicitly_wait(30)
    #wait = WebDriverWait(driver, 30)

    # Pull list of properties from website
    if test_flag:
        props = obtain_props(pwin).head(5)  # Limit to 5 properties for testing
    else:
        props = obtain_props(pwin)
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
                # print(tm)

                # Query property details
                # tm = '7-11-07-067.00'
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
                    # account = 'NaN'  # Currently highjacking this column for address 2
                    owner = attr['OwnerName']
                    subdiv = attr['SUBDIVISION']
                    tax_dist = attr['District']
                    bedrooms = 'NaN'
                    #sale_price = attr['SALE_PRICE']
                    #sale_date = from_excel_serial(attr['SaleDate'] / 86400 / 1000 + 25569)
                    yr_built = attr['YearBuilt']

                    # Calculated parameters
                    corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
                    acres = polygon_area(corners)

                    wkid = output['spatialReference']['latestWkid']
                    lat, lon = geo_convert(corners['x'].mean(), corners['y'].mean(), wkid)

                    address = reverse_geo(lat, lon)

                    bbox = box_maker(corners)
                    withdrawn = 'A'

                    # Pull additional data from the qpublic site
                    url = 'https://qpublic.schneidercorp.com/Application.aspx?AppID=857&LayerID=16069&PageTypeID=4&PageID=7149&Q=692867197&KeyValue='
                    url = url + tm

                    driver = Chrome(options=options)
                    # Set an implicit wait of 5 seconds to allow time for elements to appear before throwing an exception - waits up to 5 seconds, not a min wait time like sleep
                    driver.implicitly_wait(30)

                    driver.get(url)
                    #wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section#ctlBodyPane_ctl00_mSection')))


                    #Address - put in account for testing purposes
                    account = pull_data(driver,
                                        '//*[@id="ctlBodyPane_ctl00_ctl01_dynamicSummary_rptrDynamicColumns_ctl07_pnlSingleValue"]')
                    sq_ft = float(pull_data(driver,
                                            '//*[@id="ctlBodyPane_ctl06_ctl01_frmView_ctl00_lblFinishedSqFt"]'))  # Residential properties
                    if math.isnan(sq_ft):
                        sq_ft = float(pull_data(driver,
                                                '//*[@id="ctlBodyPane_ctl07_ctl01_frmView_ctl00_lblFinishedSqFt"]'))  # Commercial properties
                    subdiv = pull_data(driver,
                                            '// *[ @ id = "ctlBodyPane_ctl00_ctl01_dynamicSummary_rptrDynamicColumns_ctl09_pnlSingleValue"]')  # Residential properties

                    condition = pull_data(driver, '//*[@id="ctlBodyPane_ctl06_ctl01_frmView_ctl00_lblCondition"]')
                    if condition == 'NaN':
                        condition = pull_data(driver, '//*[@id="ctlBodyPane_ctl07_ctl01_frmView_ctl00_lblCondition"]')

                    bldg_type = pull_data(driver,
                                          '//*[@id="ctlBodyPane_ctl00_ctl01_dynamicSummary_rptrDynamicColumns_ctl10_pnlSingleValue"]')
                    if '(' in bldg_type and ')' in bldg_type:
                        landuse = bldg_type[bldg_type.find(start := '(') + len(start):bldg_type.find(')')]
                    else:
                        landuse = 'NaN'
                    bldgs = pull_data(driver, '//*[@id="ctlBodyPane_ctl04_ctl01_gvwFees"]/tbody/tr/td[1]')
                    if bldgs == 'NaN':
                        bldgs = '0'

                    sale_date = pull_data(driver, '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[1]/th')
                    sale_price = float(pull_data(driver, '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[1]/td[1]'))
                    if sale_price < 11:
                        sd1 = pull_data(driver, '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[2]/th')
                        sp1 = float(pull_data(driver, '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[2]/td[1]'))
                        if sp1 > 11:
                            sale_price = sp1
                            sale_date = sd1

                    appraised_land = float(
                        pull_data(driver, '//*[@id="ctlBodyPane_ctl03_ctl01_grdValuation"]/tbody/tr[1]/td[2]'))
                    appraised_bldg = float(
                        pull_data(driver, '//*[@id="ctlBodyPane_ctl03_ctl01_grdValuation"]/tbody/tr[2]/td[2]'))

                    driver.quit()

                    appraised_total = appraised_land + appraised_bldg
                    dpsf = dpsf_calc(appraised_total, sq_ft)

                    if math.isnan(appraised_land) or math.isnan(appraised_bldg):
                        bldg_ratio = float('NaN')
                    else:
                        bldg_ratio = round(appraised_bldg/appraised_total,2)

                    county_link = '=HYPERLINK("https://propertyviewer.andersoncountysc.org/mapsjs/?TMS=' + tm + '&disclaimer=false","County")'
                    map_link = '=HYPERLINK("http://maps.google.com/maps?t=k&q=loc:' + str(lat) + '+' + str(lon) + '","Map")'

                    #            'item',             'taxmap', 'account', 'owner',                    'address', 'subdiv', 'tax_dist',
                    #            'bldgs', 'acres', 'land_use','bldg_type', 'bedrooms', 'sq_ft', 'dpsf', 'yr_built','appraised_land', 'appraised_bldg', 'appraised_total',
                    #             'bldg_ratio', 'sale_price', 'sale_date', 'lake%', 'bbox', 'lat', 'lon', 'dist1', 'dist2', 'dist3', 'withdrawn', 'county_link', 'map_link',
                    #            'amount_due', 'comments', 'rating', 'bid'
                    data_list = [item, tm, account, owner, address, subdiv, tax_dist,
                        bldgs, acres, landuse, bldg_type, bedrooms, sq_ft, dpsf, yr_built, appraised_land, appraised_bldg, appraised_total,
                        bldg_ratio, sale_price, sale_date, 'NaN', bbox, lat, lon, 'NaN', 'NaN', 'NaN', withdrawn, county_link, map_link,
                        'NaN', '', '', '']

                    props_new.loc[0] = data_list
                    props_new.to_csv(filename, mode='a', index=False, header=False)
        else: # if tm is already found... occurs when you need to restart
            prop_count += 1

    driver.quit()

    return prop_count


def update_withdrawn(pwin, filename, test_flag):

    # Pull list of properties from website
    if test_flag:
        props = obtain_props(pwin).head(3)  # Limit to 3 properties for testing
    else:
        props = obtain_props(pwin)

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



