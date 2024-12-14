# -*- coding: utf-8 -*-
"""
This is the has overall logic for looking up country information - it calls county specific functions

@author: ericd
"""
import os

from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from datetime import date
from Utils.tax_util import *
from Utils.google_util import *


def obtain_props(self, county):
    import io

    self.print_text('Retrieving tax sale properties ...')
    if county == 'greenville':
        req = requests.get('https://www.greenvillecounty.org/appsAS400/Taxsale/')
        soup = BeautifulSoup(req.content, 'html.parser')
        a = soup.find_all('table')
        props = pd.read_html(io.StringIO(str(a)))[0]   # Item #, Map #, Name, Amount Due
        props.columns = ['item', 'taxmap', 'owner', 'amount_due']  # Translate into standard names

    elif county == 'anderson':
        cols = ['item', 'owner', 'tax_dist', 'prop_desc', 'taxmap', 'owner2', 'deedbook', 'page', 'yearsdue',
                'amount_due', 'pct', 'blank1', 'blank2']  # Translate into standard names
        with open('Counties/Anderson/NewspaperAd.csv') as f:
            test_prop = f.readlines()

        with open('counties/Anderson/NewspaperAd_cleaned.csv', 'w') as out:
            for line in range(len(test_prop)):
                if test_prop[line][0].isdigit():
                    out.write(test_prop[line])

        props = pd.read_csv('Counties/Anderson/NewspaperAd_cleaned.csv', sep=',', dtype=str, names=cols)

        # Remove the leading zeros and convert back to str for compatibility with later steps
        props['taxmap'] = props['taxmap'].astype('int64')
        props['taxmap'] = props['taxmap'].astype(str)

    elif county == 'spartanburg':
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

    else:
        self.print_text('The county ' + county + ' has not been defined')

    self.print_text(str(len(props)) + ' tax sale properties has been retrieved...')
    return props


def get_props(county, tm):
    if county == 'greenville':
        params = {
            'f': 'json',
            'where': "PIN = '" + tm + "'",
            'outFields': '*'
        }
        url = 'https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/53/query?'
    elif county == 'anderson':
        params = {
            'f': 'json',
            'where': "TMS = '" + tm + "'",
            'outFields': '*'
        }
        url = 'https://propertyviewer.andersoncountysc.org/arcgis/rest/services/NewPropertyViewer/MapServer/5/query?'
    elif county == 'spartanburg':
        params = {
            'f': 'json',
            'where': "MAPNUMBER = '" + tm + "'",
            'outFields': '*'
        }
        url = 'https://maps.spartanburgcounty.org/server/rest/services/OneMap/Tax_Parcels/MapServer/1/query?'
    else:
        return 0

    response = run_query(url, params)
    return json.loads(response.text)


def populate_fields(county, tm, prop, props, output):
    attr = output['features'][0]['attributes']
    corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
    wkid = output['spatialReference']['latestWkid']

    lat, lon = geo_convert(corners['x'].mean(), corners['y'].mean(), wkid)
    address = reverse_geo(lat, lon)
    if isinstance(address, str):  # Found address, NaN show up as float
        link_address = ('https://www.google.com/maps/place/' +
                        address.split()[0].replace('+', '%2B') + ',+' +
                        address.split(',')[0].split()[1].replace(' ', '+') + ',+' +
                        address.split(',')[1].strip())
    else:
        link_address = 'http://maps.google.com/maps?t=k&q=loc:' + str(lat) + '+' + str(lon)
    map_link = ('=HYPERLINK("' + link_address + '","Map")')

    bbox = box_maker(corners)
    withdrawn = 'A'
    lake, dist1, dist2, dist3 = 'NaN', 'NaN', 'NaN', 'NaN'

    if county == 'greenville':
        account = 'NaN'
        subdiv = attr['SUBDIV']
        tax_dist = attr['DIST']
        acres = attr['TACRES']
        landuse = attr['LANDUSE']
        # This doesn't work, always goes to 1, maybe landuse is a text?
        if landuse == 1180 or landuse == 9171 or landuse == 6800:
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
        # bldg_type = attr['PROPTYPE']  # Discontinued in 2024
        bedrooms = attr['BEDROOMS']
        sq_ft = attr['SQFEET']
        appraised_total = attr['FAIRMKTVAL']
        sale_price = attr['SLPRICE']
        sale_date = from_excel_serial(attr['DEEDDATE'] / 86400 / 1000 + 25569)
        bldg_type = 'NaN'
        yr_built = 'NaN'
        appraised_land = 'NaN'
        appraised_bldg = 'NaN'
        bldg_ratio = 'NaN'

        # Calculated parameters
        dpsf = dpsf_calc(appraised_total, sq_ft)

        if acres < 0.1:  # Only overwrite if acres wasn't defined
            acres = polygon_area(corners)

        county_link = '=HYPERLINK("https://www.gcgis.org/apps/GreenvilleJS/?PIN=' + tm + '","County")'

    elif county == 'anderson':
        account = 'NaN'
        subdiv = 'NaN'
        tax_dist = props['tax_dist'].iloc[prop]
        acres = attr['SHAPE.STArea()'] / 43560
        landuse = 'NaN'
        bldg_type = 'NaN'
        bedrooms = 'NaN'
        sq_ft = 'NaN'
        appraised_total = attr['MRKT_VALUE']
        bldgs = attr['IMPRV']
        yr_built = 'NaN'
        dpsf = 'NaN'  # Hard code to NaN since sq_ft not available for this county

        # Call second website for additional details
        tm2 = tm.rjust(11, '0') + props['owner2'].iloc[prop].rjust(5, '0')

        params = {'mapno': tm2}
        url = 'https://acpass.andersoncountysc.org/asrdetails.cgs?'
        response = run_query(url, params)

        soup = BeautifulSoup(response.content, 'html.parser')

        sp1 = 0
        sp2 = 0
        # Initialize variables
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
        appraised_land, appraised_bldg, asmt_total, bldg_ratio = 'NaN', 'NaN', 'NaN', 'NaN'
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
                    bldg_ratio = round(int(appraised_land) / int(asmt_total), 2)

        county_link = '=HYPERLINK("https://propertyviewer.andersoncountysc.org/mapsjs/?TMS=' + tm + '&disclaimer=false","County")'

    elif county == 'spartanburg':
        pass

    data_list = [props['item'].iloc[prop], tm, account, props['owner'].iloc[prop], address, subdiv, tax_dist,
                 bldgs, acres, landuse, bldg_type, bedrooms, sq_ft, dpsf, yr_built, appraised_land, appraised_bldg,
                 appraised_total, bldg_ratio, sale_price, sale_date, lake, bbox, lat, lon, dist1, dist2, dist3,
                 withdrawn, county_link, map_link, float(props['amount_due'].iloc[prop].strip('$').replace(',', '')),
                 '', '', '']

    return data_list


def get_gis_info(self, county, filename, test_flag):

    # Pull list of properties from website
    if test_flag:
        props = obtain_props(self, county).head(5)  # Limit to 5 properties for testing
    else:
        props = obtain_props(self, county)
    total_count = len(props)

    cols = get_cols()
    props_new = pd.DataFrame(columns=cols)

    if Path(filename).is_file():
        props_old = pd.read_csv(filename, sep=',', dtype=get_type())
    else:
        props_new.to_csv(filename, index=False)  # Write out headers
        # Creates empty dataframe to compare to, won't find anything and will write out all taxmaps
        props_old = pd.DataFrame(columns=['taxmap'])

    prop_count = 0
    t0 = time.perf_counter()
    dt = []
    for prop in props.index:

        tm = props['taxmap'].iloc[prop]
        if not (props_old['taxmap'].eq(tm)).any():

            if len(str(tm)) > 5:  # Check for valid TaxMap ID
                # print(tm)

                output = get_props(county, tm)

                prop_count += 1
                t1 = time.perf_counter()
                dt.append(t1 - t0)
                t0 = t1
                est_time_left = sum(dt) / len(dt) * (total_count - prop_count)
                self.print_text('{0}/{1}  Tax map ID: {2} Estimated time remaining = {3}s'
                                .format(str(prop_count), str(total_count), str(tm), int(est_time_left)))

                if len(output['features']) == 0:  # Didn't get something back from the website
                    pass
                    props_new.loc[0] = 'NaN'  # Fill with NaN
                    props_new['item'].loc[0] = props['item'].iloc[prop]
                    props_new['taxmap'].loc[0] = tm
                    props_new['owner'].loc[0] = props['owner'].iloc[prop]
                    props_new.to_csv(filename, mode='a', index=False, header=False)

                else:
                    data_list = populate_fields(county, tm, prop, props, output)
                    props_new.loc[0] = data_list
                    props_new.to_csv(filename, mode='a', index=False, header=False)

        else:  # if tm is already found... occurs when you need to restart
            prop_count += 1

    return prop_count


def update_withdrawn(self, county, filename, test_flag):

    # Pull list of properties from website
    if test_flag:
        props = obtain_props(self, county).head(3)  # Limit to 5 properties for testing
    else:
        props = obtain_props(self, county)

    if Path(filename).is_file():
        props_main = pd.read_csv(filename, sep=',', dtype=get_type())
        initial_count = props_main['withdrawn'].value_counts()['A']
        props_main['withdrawn'] = 'W'   # Set all to withdrawn
        props['withdrawn'] = 'A'   # Set all remaining properties to available
        props_main.set_index('item', inplace=True)
        props.set_index('item', inplace=True)
        props_main['withdrawn'].update(props['withdrawn'])
        props_main.reset_index(drop=False, names='item', inplace=True)
        new_count = props_main['withdrawn'].value_counts()['A']
        withdrawn_count = initial_count - new_count

        props_main.to_csv(filename, index=False, na_rep='NaN')

    else:
        withdrawn_count = 0
        new_count = 0
        self.print_text('Opps!  You need to read properties first!')

    return new_count, withdrawn_count


def lake_url(county, bbox):
    if county == 'greenville':
        url = ('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96'
               '&transparent=true&format=png8&layers=show%3A53%2C49%2C48&bbox=')
        url = url + bbox
        return url + '&bboxSR=6570&imageSR=6570&size=937%2C955&f=image'
    elif county == 'anderson':
        url = ('https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Overlays/MapServer/export?dpi=96'
               '&transparent=true&format=png8&layers=show%3A1&bbox=')
        url = url + bbox
        return url + '&bboxSR=102733&imageSR=102733&size=759%2C885&f=image'
    elif county == 'spartanburg':
        return 0  # Not set up for spartanburg yet


def county_pic_url(county, bbox):
    if county == 'greenville':
        """
        Layer   Description
        0       Symbols
        17      Swamp Rabbet Trail
        35      Lot numbers
        38      Railroad Tracks
        41      Street Names
        47, 48  Water
        49      Colored backgrounds
        50      Red former property lines
        52      Property lines
        
        58, 59, 60, 61, 62, 63, 64, 66 - Might be flood plain

        2, 3, 4, 5, 16, 39, 40, 43, 78  Empty (at least for test map)
        """
        url = ('https://www.gcgis.org/arcgis/rest/services/GreenvilleJS/Map_Layers_JS/MapServer/export?dpi=96'
               '&transparent=true&format=png8&layers=show%3A52%2C0%2C17%2C38%2C41%2C47%2C48&bbox=')
        url = url + bbox
        return url + '&bboxSR=6570&imageSR=6570&size=600%2C400&f=image'
    elif county == 'anderson':
        url = ('https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Overlays/MapServer/export?dpi=96'
               '&transparent=true&format=png8&layers=show%3A1&bbox=')
        url = url + bbox
        return url + '&bboxSR=102733&imageSR=102733&size=759%2C885&f=image'
    elif county == 'spartanburg':
        return 0  # Not set up for spartanburg yet


def set_lake_params(county):
    if county == 'greenville':
        return 0, 'inv'
    elif county == 'anderson':
        return 1, 'norm'
    elif county == 'spartanburg':
        return 0, 'inv'  # Hasn't been established yet, just placeholder values


def find_lake_props(self, county, filename):
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

        lake_val = []
        t0 = time.perf_counter()
        dt = []
        count = 0
        total_count = len(props)
        for index, bbox in props['bbox'].items():
            count += 1
            t1 = time.perf_counter()
            dt.append(t1 - t0)
            t0 = t1
            est_time_left = sum(dt) / len(dt) * (total_count - count)
            self.print_text('Finding lake percentages for property {0}/{1}: Estimated time remaining = {2}s'
                       .format(str(count), str(total_count), int(est_time_left)))

            if isinstance(bbox, float):  # NaN will be a float, expecting a string
                lake_val.append('NaN')
            else:
                url = lake_url(county, bbox)
                img = Image.open(urlopen(url))
                pixel_count = img.size[0] * img.size[1]
                img_list = list(img.getdata())
                # These statements can help dig into the details of the image to figure out how lakes are ID'd
                # print(img.mode, img.size, img.info, img.getbands())
                # img2 = img.convert('RGB')
                # img.show()
                # print([img_list.count(x) for x in range(max(img_list))])

                lake_pixel, lake_calc = set_lake_params(county)
                lake_count = img_list.count(lake_pixel)
                if lake_calc == 'norm':
                    lake_val.append((lake_count / pixel_count) * 100)
                elif lake_calc == 'inv':
                    lake_val.append((1 - lake_count / pixel_count) * 100)

        props['lake%'] = lake_val
        props.to_csv(filename, index=False, na_rep='NaN')

        return True

    else:
        self.print_text("Properties haven't been found yet, need to do that before finding lake properties")
        return False


def get_county_pictures(taxmap, county, bbox):
    from urllib.request import urlopen
    from PIL import Image

    if not os.path.isfile('Counties/' + county.title() + '/CountyView/' + taxmap + '.png'):
        url = county_pic_url(county, bbox)
        img = Image.open(urlopen(url))
        img = img.convert("RGB")
        img.save('Counties/' + county.title() + '/CountyView/' + taxmap + '.png')

    # img.show()

    return
