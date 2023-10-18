# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 19:42:28 2022

@author: ericd
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 14:28:51 2022

Copy property data from Spartangbug county website into props_raw.txt, no cleanup neaded

@author: ericd
"""

import requests
import json
import pandas as pd
import math
import time
from pathlib import Path

def read_props():
    
    filename = 'props_raw.csv'
    with open(filename) as f:
        props = f.readlines()
    
    props[0] = 'ITEM,TAXMAP,DESCRIPTION\n'  #Set the header
            
    for i in range(1, len(props)):
        props[i] = props[i].replace(',', '')
        if props[i][0:4].isnumeric():
            props[i] = props[i].replace(' ', ',', 2)   #Adds a comma after the first space
        else:
            props[i-1] = props[i-1].rstrip() #Removes the carriage return from the previous line, lines will get combined at export
            
    out = open('props_clean.csv', 'w')           
    for line in props:
        out.write(line)
    out.close() 

def MetersToLatLon(mx, my):
    "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"
    originShift = 2 * math.pi * 6378137 / 2.0
    lon = (mx / originShift) * 180.0
    lat = (my / originShift) * 180.0

    lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lon


def reversegeo(lat, lon):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng='
    url = url + str(lat) + ',' + str(lon)
    key = '&key=AIzaSyDyd3zu8GJTNQ18XizFNYKi9b0Ut7V472c'
    
    url = url + key
    #print(url)
    
    payload={}
    headers = {}
    
    response = requests.request("GET", url, headers=headers, data=payload)
    
    #print(response.text)
    output = json.loads(response.text)
    #print(output)

    if output['status'] == 'OK':
        add1 = output['plus_code']['compound_code']   #Actual center of property
        #add2 = output['results'][0]['formatted_address']  #Closest actual address - could be misleading, for reference
    else:
        add1 = 'Failed'
    return add1 


###############################################################################
###############################################################################
#Start of Main code

#Controls is the distance loop is run, helps keep cost down
find_distance = False   

read_props()
props = pd.read_csv('props_clean.csv')

filename = 'props_out.csv'
col_list = ['ITEM', 'TAXMAP', 'DESCRIPTION', 'address', 'sale_price', 'sale_date', 'appraised_land', 'appraised_bldg', 'appraised_total', 'bldg_ratio', 'acres', 'acres_area', 'subdiv', 'prop_type', 'land_use', 'bldg_type', 'yr_built', 'sq_ft', 'dpsf', 'dist', 'county_link', 'maps_link']
props_new = pd.DataFrame(columns = col_list)

if Path(filename).is_file():
    props_old = pd.read_csv(filename, sep=',', dtype=str)    
else:
    props_new.to_csv(filename, index = False)   #Write out headers
    props_old = pd.DataFrame(columns = ['TAXMAP'])  #Creates empty dataframe to compare to, won't find anything and will write out all taxmaps


for prop in props.index:
       
    tm = props['TAXMAP'].iloc[prop]
    if not (props_old['TAXMAP'].eq(tm)).any():

        if len(tm) < 10:  #Check for invalid TaxMap ID
            props_new.loc[0] = 'NaN'    #Fill with NaN
            props_new.to_csv(filename, mode='a', index=False, header=False)    

        else:
            print(tm) 
            
            #Query property details
            url = 'https://maps.spartanburgcounty.org/server/rest/services/Production/Parcels_and_Subdivisions/MapServer/3/query?f=json&where=UPPER(Addressing.SDE.Parcel.MAPNUMBER)%20LIKE%20%27%25'
            url = url + tm + '%25%27&returnGeometry=true&spatialRel=esriSpatialRelIntersects&maxAllowableOffset=1&outFields=*&outSR=102100'
            #url = 'https://maps.spartanburgcounty.org/server/rest/services/parcel_map_lay/MapServer/3/query?f=json&where=UPPER(Addressing.SDE.Parcel.MAPNUMBER)%20LIKE%20%27%25'
            #url = url + tm + '%25%27&returnGeometry=true&spatialRel=esriSpatialRelIntersects&maxAllowableOffset=1&outFields=*&outSR=102100'
                        
            payload={}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            output = json.loads(response.text)
            #print(output['features'][0]['attributes'].items())
            #print(output['features'][0]['geometry']['rings'][0])
            
            if len(output['features']) == 0:  #Didn't get something back from the website
                props_new.loc[0] = 'NaN'    #Fill with NaN
                props_new.to_csv(filename, mode='a', index=False, header=False)    

            else:              
                attr = output['features'][0]['attributes']
                #print(attr)

                address = attr['sde.SDE.CAMA.PropertyLocation']
                sale_price = attr['sde.SDE.CAMA.SaleAmount']
                sale_date = attr['sde.SDE.CAMA.SaleDate']
                if sale_date  is None or sale_date  < 0:
                    sale_date = 'NaN'
                else:
                    sale_date = time.strftime('%Y-%m-%d', time.gmtime(sale_date /1000))
                appraised_land = attr['sde.SDE.CAMA.PreviousAppraisedLandValue']
                appraised_bldg = attr['sde.SDE.CAMA.PreviousAppraisedBuildingValue']
                if appraised_land  is None or appraised_bldg  is None:
                    appraised_total = 'NaN'
                    bldg_ratio = 'NaN'
                else: 
                    appraised_total = appraised_bldg + appraised_land
                    if appraised_total > 0:
                        bldg_ratio = round(appraised_bldg / appraised_total,2)
                    else:
                        bldg_ratio = 0
                acres = attr['Addressing.SDE.Parcel.DEEDACREAGE']
                if acres is None:
                    acres_area = 'NaN'
                else:
                    acres_area = round(attr['Shape.STArea()'] / 43560, 2)

                subdiv = attr['Addressing.SDE.Parcel.SUBDIVISION']
                prop_type = attr['sde.SDE.CAMA.PropertyType']
                land_use = attr['sde.SDE.CAMA.LandUse']
                bldg_type = attr['sde.SDE.CAMA.BuildingType']
                yr_built = attr['sde.SDE.CAMA.YearBuilt']
                sq_ft = attr['sde.SDE.CAMA.LivingArea']
                if sq_ft is not None and sq_ft > 0:
                    dpsf = round(appraised_total / sq_ft, 0)
                else:
                    dpsf = 'NaN'
                county_link = '=HYPERLINK("https://qpublic.schneidercorp.com/Application.aspx?AppID=857&LayerID=16069&PageTypeID=4&PageID=7149&KeyValue=' + tm + '","County")'
                
                # Find lat, long
                corners = pd.DataFrame(data = output['features'][0]['geometry']['rings'][0], columns = ['x', 'y'])
                lat, lon = MetersToLatLon(corners['x'].mean(), corners['y'].mean())

                if address is None or not address[0].isdigit or address[0] == '0':
                    address = reversegeo(lat, lon)

                #Address based map link
                maps_link = '=HYPERLINK("https://www.google.com/maps/search/?api=1&query=' + address.replace('+','%2B').replace(' ','+') + '","Map")'

                if find_distance:
                    origin = lat + ',' + lon
                    #dest = '34.50957,-82.63044'   #Location of Anderson Athletic Fields
                    dest = '34.677139,-82.836417'   #Location of Clemson - no spaces!
                    
                    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
                    origin = 'origins=' + origin.replace(" ","%20").replace(",","%2C") + '&'
                    dest = 'destinations=' + dest.replace(" ","%20").replace(",","%2C") + '&'
                    units = 'units=imperial&'
                    key = 'key=AIzaSyDyd3zu8GJTNQ18XizFNYKi9b0Ut7V472c'
                    
                    url = url + origin + dest + units + key
                    #print(url)
                    
                    payload={}
                    headers = {}
                    
                    response = requests.request("GET", url, headers=headers, data=payload)
                    
                    #print(response.text)
                    output = json.loads(response.text)
                    if output['status'] == 'OK':
                        try: 
                            dist = round(output['rows'][0]['elements'][0]['distance']['value'] / 1609, 1)   #Convert meters to miles
                        except:
                            dist = 'Failed'
                            print(output)
                    else:
                        dist = 'Failed'
                else:
                    dist = 0
                    
                data_list = [props['ITEM'].iloc[prop], tm, props['DESCRIPTION'].iloc[prop], address, sale_price, sale_date, appraised_land, appraised_bldg, appraised_total, bldg_ratio, acres, acres_area, subdiv, prop_type, land_use, bldg_type, yr_built, sq_ft, dpsf, dist, county_link, maps_link]
                props_new.loc[0] = data_list    
                props_new.to_csv(filename, mode='a', index=False, header=False)    


