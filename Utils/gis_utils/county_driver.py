# -*- coding: utf-8 -*-
"""
This is the has overall logic for looking up country information - it calls county specific functions

@author: ericd
"""
import io
import os

from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
from datetime import date
# Need to comment out for testing in the main block
from Utils.tax_util import *
from Utils.google_util import *


def obtain_props(self, county):

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
    # print(output)
    attr = output['features'][0]['attributes']
    corners = pd.DataFrame(data=output['features'][0]['geometry']['rings'][0], columns=['x', 'y'])
    wkid = output['spatialReference']['latestWkid']

    lat, lon = geo_convert(corners['x'].mean(), corners['y'].mean(), wkid)
    address = reverse_geo(lat, lon)
    if isinstance(address, str):  # Found address, NaN show up as float
        link_address = ('https://www.google.com/maps/place/' +
                        address.split()[0].replace('+', '%2B') + ',+' +
                        address.split(',')[0].split(maxsplit=1)[1].replace(' ', '+') + ',+' +
                        address.split(',')[1].strip())
    else:
        link_address = 'http://maps.google.com/maps?t=k&q=loc:' + str(lat) + '+' + str(lon)
    map_link = ('=HYPERLINK("' + link_address + '","Map")')

    bbox = box_maker(corners)
    corners_str = corners_to_text(corners)

    withdrawn = 'A'
    lake, dist1, dist2, dist3 = 'NaN', 'NaN', 'NaN', 'NaN'

    if county == 'greenville':
        account = 'NaN'
        subdiv = attr['SUBDIV']
        tax_dist = attr['DIST']
        acres = attr['TACRES']
        landuse = attr['LANDUSE']
        # This doesn't work, always goes to 1, maybe landuse is a text?
        if landuse == "1180" or landuse == "9171" or landuse == "6800":
            bldgs = 0
        else:
            bldgs = 1
        # 110: Multi-Family Duplex
        # 112: Multi-Family Multiplex
        # 330: Auto - Service Garage / Body Shop
        # 421: Office – General
        # 890: Broadcasting Facility
        # 940: Storage / Warehouse – General
        # 1100: Residential Single Family
        # 1101: Residential Single Family with Auxiliary Use
        # 1170: Residential Mobile Home with Land
        # 1171: Residential Mobile Home on Mobile Home File
        # 1180: Residential Vacant
        # 1181: Homeowners Association Property
        # 1182: Common Area
        # 6800: Commercial Vacant
        # 9170: Agricultural Vacant
        # 9171: Agricultural Improved
        # bldg_type = attr['PROPTYPE']  # Discontinued in 2024
        bedrooms = attr['BEDROOMS']
        sq_ft = attr['SQFEET']
        appraised_total = attr['FAIRMKTVAL']
        sale_price = attr['SLPRICE']
        if isinstance(attr['DEEDDATE'], int):
            sale_date = from_excel_serial(attr['DEEDDATE'] / 86400 / 1000 + 25569)
        else:
            sale_date = 'NaN'
        bldg_type = 'NaN'
        yr_built = 'NaN'
        appraised_land = 'NaN'
        appraised_bldg = 'NaN'
        bldg_ratio = 'NaN'
        # Other attributes that might be useful:  IMPROVED, PROPTYPE
        prev_owner = (attr['POWNNM'] or '').strip() or 'NaN'

        # Calculated parameters
        dpsf = dpsf_calc(appraised_total, sq_ft)

        calc_acres = polygon_area(corners)
        if acres < 0.1 or abs(calc_acres - acres) > 0.05:  # Only overwrite if acres wasn't defined
            acres = calc_acres
            bldgs = -9  # Flag indicated that calculated acres is being used

        county_link = '=HYPERLINK("https://www.gcgis.org/apps/GreenvilleNJ/?PIN=' + tm + '","County")'

    elif county == 'anderson':
        account = 'NaN'
        prev_owner = 'NaN'  # Not available from the Anderson sources
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

    amount_due = float(props['amount_due'].iloc[prop].strip('$').replace(',', ''))
    # Ths logic is that I won't be too bummed about only earning 6% but would be more bummed by not being able to bid
    max_bid = round(amount_due / 0.06, 0)  # This could have been set to amount_due / 0.12 to be more conservative
    est_bid = round(max(appraised_total, sale_price) * 0.80, 0)  # Based on past experience the bid is likely to go
    data_list = [props['item'].iloc[prop], tm, account, props['owner'].iloc[prop], prev_owner, address, subdiv, tax_dist,
                 bldgs, acres, landuse, bldg_type, bedrooms, sq_ft, dpsf, yr_built, appraised_land, appraised_bldg,
                 appraised_total, bldg_ratio, sale_price, sale_date, lake, bbox, corners_str, lat, lon, dist1, dist2, dist3,
                 withdrawn, county_link, map_link, amount_due, '', '', '', est_bid, max_bid]

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
                    defaults = get_defaults()  # Default value for each column based on its expected type
                    props_new.loc[0] = [defaults[col] for col in cols]
                    props_new.loc[0, 'item'] = props['item'].iloc[prop]
                    props_new.loc[0, 'taxmap'] = tm
                    props_new.loc[0, 'owner'] = props['owner'].iloc[prop]
                    props_new.to_csv(filename, mode='a', index=False, header=False, na_rep='NaN')

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
        """
        Browse this to find the layers
        https://www.gcgis.org/arcgis3/rest/services
        
        Layer   Description
        41      Flood Plain
        5, 6    Water - Lakes and Rivers
        """
        url = ('https://www.gcgis.org/arcgis3/rest/services/GCGIA/Greenville_Base/MapServer/export?dpi=96'
            '&transparent=true&format=png8&layers=show%3A5%2C6&bbox=')
        url = url + bbox
        url = url + '&bboxSR=6570&imageSR=6570&size=937%2C955&f=image'
        return url 
    elif county == 'anderson':
        url = ('https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Overlays/MapServer/export?dpi=96'
               '&transparent=true&format=png8&layers=show%3A1&bbox=')
        url = url + bbox
        return url + '&bboxSR=102733&imageSR=102733&size=759%2C885&f=image'
    elif county == 'spartanburg':
        return 0  # Not set up for spartanburg yet


def find_lake_props(self, county, filename):
    from urllib.request import urlopen
    from PIL import Image

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
                img = Image.open(urlopen(url)).convert('RGBA')
                pixel_count = img.size[0] * img.size[1]
                img_list = list(img.getdata())
                                
                # These statements can help dig into the details of the image to figure out how lakes are ID'd
                # print(img.mode, img.size, img.info, img.getbands())
                # img2 = img.convert('RGB')
                # img.show()
                # print([img_list.count(x) for x in range(max(img_list))])

                # Transparent pixels (alpha == 0) are background; anything else is water
                water_count = sum(1 for px in img.getdata() if px[3] > 0)
                lake_pct = water_count / pixel_count * 100
                lake_val.append(lake_pct)

        props['lake%'] = lake_val
        props.to_csv(filename, index=False, na_rep='NaN')

        return True

    else:
        self.print_text("Properties haven't been found yet, need to do that before finding lake properties")
        return False


def county_pic_url(county, bbox):
    if county == 'greenville':
        """
        Browse this to find the layers
        https://www.gcgis.org/arcgis3/rest/services
        
        Layer   Description
        41      Flood Plain
        5, 6    Water - Lakes and Rivers
        """
        url = ('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?'
               'format=png8&bbox=')
        url = url + bbox
        return url + '&bboxSR=6570&imageSR=6570&size=600%2C400&f=image'
    elif county == 'anderson':
        url = ('https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Overlays/MapServer/export?dpi=96'
               '&transparent=true&format=png8&layers=show%3A1&bbox=')
        url = url + bbox
        return url + '&bboxSR=102733&imageSR=102733&size=759%2C885&f=image'
    elif county == 'spartanburg':
        return 0  # Not set up for spartanburg yet
    else:
        return 'County Not Found'


def get_county_pictures(taxmap, county, corners, size=800, margin=0.5, line_width=3, show=False):
    # Assumes that corners is in text form and needs converted via text_to_corners()
    from urllib.request import urlopen
    from PIL import Image, ImageDraw
    import io

    corners = text_to_corners(corners)
    if not os.path.isfile('Counties/' + county.title() + '/CountyView/' + taxmap + '.png'):
        # Square bbox centered on the parcel, so the image isn't stretched
        xs = corners['x'].tolist()
        ys = corners['y'].tolist()
        half = max(max(xs) - min(xs), max(ys) - min(ys)) * (0.5 + margin)
        # World Imagery errors (HTTP 500) if zoomed in past ~1 ft per pixel, so keep the image at least size feet wide
        half = max(half, size / 2)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        xmin, ymin, xmax, ymax = cx - half, cy - half, cx + half, cy + half

        # Aerial photo (Esri World Imagery)
        aerial_url = 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export'
        params = {'bbox': f'{xmin},{ymin},{xmax},{ymax}', 'bboxSR': 6570, 'imageSR': 6570,
                'size': f'{size},{size}', 'format': 'jpg', 'f': 'image'}
        resp = requests.get(aerial_url, params=params, timeout=60)
        img = Image.open(io.BytesIO(resp.content)).convert('RGB')
        # Convert map coordinates to pixels and draw the red outline
        draw = ImageDraw.Draw(img)
        pts = [((x - xmin) / (xmax - xmin) * size, (ymax - y) / (ymax - ymin) * size) for x, y in zip(corners['x'], corners['y'])]
        draw.line(pts + [pts[0]], fill=(255, 0, 0), width=line_width)

        if show:
            img.show()
        else:
            img.save('Counties/' + county.title() + '/CountyView/' + taxmap + '.png')

    return


def locator_fraction(x, y, extent):
    # Map coordinates -> (fx, fy) position within the base map, 0-1 measured from the top-left corner
    return ((x - extent['xmin']) / (extent['xmax'] - extent['xmin']),
            (extent['ymax'] - y) / (extent['ymax'] - extent['ymin']))


def corners_center(corners):
    # Center of the parcel from its text-form corners
    from Utils.tax_util import text_to_corners
    corners = text_to_corners(corners)
    return ((corners['x'].min() + corners['x'].max()) / 2, (corners['y'].min() + corners['y'].max()) / 2)


def get_county_basemap(county, width=900, min_lake_area=2_000_000, min_city_sq_miles=3):
    """
    Builds (once) the whole-county locator map: county boundary, highways and city limits from the county's export
    service, plus large lakes and city names drawn on top (the service hides these at county scale).
    Saved as Counties/<County>/CountyBase.png with the map extent in CountyBase.json.
    Returns (png_path, extent) or None if the county isn't supported.
    """
    import json
    import io
    from PIL import Image, ImageDraw, ImageFont

    if county != 'greenville':
        return None

    folder = 'Counties/' + county.title() + '/'
    png_path, json_path = folder + 'CountyBase.png', folder + 'CountyBase.json'
    if os.path.isfile(png_path) and os.path.isfile(json_path):
        with open(json_path) as f:
            return png_path, json.load(f)

    base = 'https://www.gcgis.org/arcgis3/rest/services/GCGIA/Greenville_Base/MapServer'
    # Layers: 16 County Boundary, 1 Federal Highway, 14 Municipal Boundary, 6 Lake or River
    resp = requests.get(base + '/16/query', verify=False, timeout=60,
                        params={'f': 'json', 'where': '1=1', 'returnExtentOnly': 'true', 'outSR': 6570})
    ext = resp.json()['extent']
    pad = 0.03 * max(ext['xmax'] - ext['xmin'], ext['ymax'] - ext['ymin'])
    extent = {'xmin': ext['xmin'] - pad, 'ymin': ext['ymin'] - pad, 'xmax': ext['xmax'] + pad, 'ymax': ext['ymax'] + pad}
    height = round(width * (extent['ymax'] - extent['ymin']) / (extent['xmax'] - extent['xmin']))
    extent.update({'width': width, 'height': height})

    params = {'bbox': f"{extent['xmin']},{extent['ymin']},{extent['xmax']},{extent['ymax']}", 'bboxSR': 6570,
              'imageSR': 6570, 'size': f'{width},{height}', 'format': 'png', 'transparent': 'false',
              'layers': 'show:16,1,14', 'f': 'image'}
    img = Image.open(io.BytesIO(requests.get(base + '/export', params=params, verify=False, timeout=120).content))
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)

    def to_px(point):
        fx, fy = locator_fraction(point[0], point[1], extent)
        return fx * width, fy * height

    # Large lakes only - the layer also holds thousands of ponds and streams
    resp = requests.get(base + '/6/query', verify=False, timeout=120,
                        params={'f': 'json', 'where': f'Shape.STArea() > {min_lake_area}', 'outFields': 'OBJECTID',
                                'returnGeometry': 'true', 'outSR': 6570, 'maxAllowableOffset': 50})
    for feature in resp.json().get('features', []):
        for ring in feature['geometry']['rings']:
            draw.polygon([to_px(p) for p in ring], fill=(110, 165, 225), outline=(70, 120, 190))

    # City names, placed on the largest piece of each city
    resp = requests.get(base + '/14/query', verify=False, timeout=120,
                        params={'f': 'json', 'where': f'SQMILES > {min_city_sq_miles}', 'outFields': 'NAME,SQMILES',
                                'returnGeometry': 'true', 'outSR': 6570, 'maxAllowableOffset': 100})
    try:
        font = ImageFont.truetype('arial.ttf', 15)
    except OSError:
        font = ImageFont.load_default()
    for feature in resp.json().get('features', []):
        xs, ys = zip(*[p for ring in feature['geometry']['rings'] for p in ring])
        cx, cy = to_px(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
        name = feature['attributes']['NAME'].title()
        left, top, right, bottom = draw.textbbox((0, 0), name, font=font)
        draw.text((cx - (right - left) / 2, cy - (bottom - top) / 2), name, fill=(40, 40, 40), font=font,
                  stroke_width=2, stroke_fill=(255, 255, 255))

    os.makedirs(folder, exist_ok=True)
    img.save(png_path)
    with open(json_path, 'w') as f:
        json.dump(extent, f)
    return png_path, extent


if __name__ == '__main__':
    # This section is used for testing algorithms
    # Need to comment out the util import lines at the top of the file to run
    
    import os
    import io
    import sys
    print(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Up one directory, so Utils is found
    from tax_util import *
    from google_util import *

    county = "greenville"
    taxmap = "0376000105000"
    margin = 0.5  # Default margin is 0.5
    size = 800      # Default size is 800
    line_width = 3  # Default line width is 3

    # Comment this line out to use taxmap instead of corners_str; 
    corners_str = '1647645.6669947505 1069640.1066273004;1647649.0679133832 1069637.730314955;1647649.3999343812 1069637.4983595759;1647710.7201443613 1069594.6443569511;1647807.5049212575 1069527.0068897605;1647651.4970472455 1069369.8487532735;1647788.8038057685 1069241.7545931786;1647948.9540682435 1069404.0715223104;1648568.8057742715 1068968.5666010529;1648524.222769022 1068912.1286089271;1648374.144685045 1068738.3415354341;1648223.3267716467 1068575.9475065619;1648125.4957349151 1068478.3959973752;1648031.6617454141 1068388.2585301846;1647469.333989501 1067869.7086614221;1647012.2575459331 1068135.039041996;1647013.2588582635 1068143.1479658782;1647050.664041996 1068446.0672572106;1647157.3930446208 1068830.019685045;1647226.9612860829 1069080.2801837325;1647129.7995406836 1069271.1827427894;1647237.1138451397 1069349.0318241417;1647312.140748039 1069405.0531496108;1647321.152230978 1069411.7818241417;1647610.8333333284 1069628.0836614221;1647612.2257217914 1069629.1233595759;1647646.2260498703 1069654.5108267665;1647645.8543307036 1069644.933727041;1647645.6669947505 1069640.1066273004'
    if 'corners_str' not in locals():
        parcel_url = ('https://www.gcgis.org/arcgis3/rest/services/GreenvilleNJ/Tax_Parcel_Search_and_Select/'
                    'MapServer/0/query')
        params = {'f': 'json', 'where': "PIN = '" + taxmap + "'", 'outFields': 'PIN', 'outSR': 6570,
                'returnGeometry': 'true'}
        features = requests.get(parcel_url, params=params, timeout=60).json().get('features', [])
        corners = pd.DataFrame(data=features[0]['geometry']['rings'][0], columns=['x', 'y'])
        corners_str = corners_to_text(corners)
    
    get_county_pictures(taxmap, county, corners_str, size=size, margin=margin, line_width=line_width, show=True)

