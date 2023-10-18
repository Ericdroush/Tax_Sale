# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 14:28:51 2022


NOT FINISHED!

@author: ericd
"""

import requests
import json
import pandas as pd
import math
import re

find_distance = False   #Turned this off to query more details from Anderson County site
dist = []
address = []
sale_price = []
sale_date = []
market = []
acres = []
imprv = []
ratio = [] #Don't know what this is, suspect it's residential, commercial, etc

mh_screen = 4000000000
filename = 'props.csv'
props = pd.read_csv(filename)

for tm in props.TAXMAP:
    if math.isnan(tm):
        dist.append('NaN')
        address.append('NaN')
        sale_price.append('NaN')
        sale_date.append('NaN')
        market.append('NaN')
        acres.append('NaN')
        imprv.append('NaN')
        ratio.append('NaN') 

    else:
        if tm > mh_screen:
            dist.append("MH")
            address.append("MH")
            sale_price.append("MH")
            sale_date.append("MH")
            market.append("MH")
            acres.append("MH")
            imprv.append("MH")
            ratio.append("MH")
        else:
            tm = str(int(tm))
            print(tm)
            
            #Query property details
            url = 'https://arcserver2.oconeesc.com/arcgis/rest/services/PARCELDATA/MapServer/1/query?f=json&where=UPPER(TMS_NUMBER)%20LIKE%20%27%25'
            url = url + tm + '%25%27&outFields=*'
            
            payload={}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            output = json.loads(response.text)
            
            if len(output['features']) == 0:
                address.append('NA')
                sale_price.append('NA')
                sale_date.append('NA')
                market.append('NA')
                acres.append('NA')
                imprv.append('NA')
                ratio.append('NA')
            else:              
                attr = output['features'][0]['attributes']
                #print(attr)
                
                addr = attr['PHYS_ADDR']
                sale_price.append(attr['SALE_PRICE'])
                sale_date.append(attr['SALE_YEAR'])
                market.append(attr['MRKT_VALUE'])
                acres.append(attr['SHAPE.STArea()'] / 43560)
                imprv.append(attr['IMPRV'])
                ratio.append(attr['RATIO'])
                
                #Trim out the neighborhood from the address
                if len(addr) > 0:
                    i = re.search(r"\d", addr)
                    if i:
                        address.append(addr[i.start():len(addr)])
                    else:
                        address.append('NA')                    
                else:
                    address.append('NA')
                
                # Find lat, long
                corners = pd.DataFrame(data = output['features'][0]['geometry']['rings'][0], columns = ['x', 'y'])
                url = 'https://propertyviewer.andersoncountysc.org/arcgis/rest/services/Utilities/Geometry/GeometryServer/project?f=json&outSR=4326&inSR=102733&geometries=%7B%22geometryType%22%3A%22esriGeometryPoint%22%2C%22geometries%22%3A%5B%7B%22x%22%3A'
                url = url + str(corners['x'].mean()) + '%2C%22y%22%3A' + str(corners['y'].mean()) + '%2C%22spatialReference%22%3A%7B%22wkid%22%3A102733%2C%22latestWkid%22%3A102733%7D%7D%5D%7D&dojo.preventCache=1665947966925'
                
                payload={}
                headers = {}
                response = requests.request("GET", url, headers=headers, data=payload)
                output = json.loads(response.text)
                
                long = output['geometries'][0]['x']
                lat = output['geometries'][0]['y']
                #print(long, lat)
                if find_distance:
                    origin = lat + ',' + long
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
                            dist.append(round(output['rows'][0]['elements'][0]['distance']['value'] / 1609, 1))   #Convert meters to miles
                        except:
                            dist.append('Failed')
                            print(output)
                    else:
                        dist.append('Failed')

if find_distance:
    props['Distance'] = dist

props['Address'] = address
props['sale_price'] = sale_price
props['sale_date'] = sale_date
props['Market'] = market
props['acres'] = acres
props['imprv'] = imprv
props['ratio'] = ratio

props.to_csv(filename.replace(".csv","_out2.csv"), index = False)    
