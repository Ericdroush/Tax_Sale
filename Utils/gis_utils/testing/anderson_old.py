# -*- coding: utf-8 -*-
"""
Created on Mon Sep 19 19:52:57 2022

0.  Finish writing anderson2.py - it basically only needs to read props.csv and loop

1.  Export properties as .csv file named props.csv
2.  Run this script
3.  Copy props.csv_out into Excel


@author: ericd
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import math

find_distance = False   #Turned this off to query more details from Anderson County site
dist = []
address = []
sale_price = []
sale_date = []
market = []
acres = []
bldgs = []
landasmt = []


#For future efforts - link to map
# https://propertyviewer.andersoncountysc.org/mapsjs/?TMS=1491606003&disclaimer=false

mh_screen = 4000000000
filename = 'props.csv'
props = pd.read_csv(filename)

for tm in props.TAXMAP:
    if math.isnan(tm):
        dist.append("NaN")
        address.append("NaN")
        sale_price.append("NaN")
        sale_date.append("NaN")
        market.append("NaN")
        acres.append("NaN")
        bldgs.append("NaN")
        landasmt.append("NaN")

    else:
        if tm > mh_screen:
            dist.append("MH")
            address.append("MH")
            sale_price.append("MH")
            sale_date.append("MH")
            market.append("MH")
            acres.append("MH")
            bldgs.append("MH")
            landasmt.append("MH")
        else:
            tm = str(int(tm))
            print(tm)
            
            if len(tm) == 9:
                tm = '00' + tm + '00000'
            else:
                tm = '0' + tm + '00000'
                       
            req = requests.get('https://acpass.andersoncountysc.org/asrdetails.cgs?mapno=' + tm)
            soup = BeautifulSoup(req.content, 'html.parser')
            
            mail_address = ""        
            for a in soup.find_all('td', text='Address'):
                mail_address = a.parent.get_text().split('\n')[2]
                break
            
            city = ""
            state = ""
            for a in soup.find_all('td', text='City, State'):
                city = a.parent.get_text().split('\n')[2].split()[0]
                state = a.parent.get_text().split('\n')[2].split()[1]
                break
            
            phys_address = ""
            for a in soup.find_all('td', text='Market Value'):
                phys_address = a.parent.get_text().split('\n')[3]
                b = a.parent.get_text().split('\n')[5].replace(',','')
                break
            if len(b) > 0:
                market.append(b)
            else:
                market.append('NA')
 
            sp1 = 0
            sp2 = 0            
            for a in soup.find_all('td', text='Date'):
                b = a.parent.find_next('tr').get_text()
                if b.count('\n') > 4:   #This line has sales dat
                    sd1 = b.split('\n')[1]
                    c = b.split('\n')[4].replace('$','').replace(',','').strip()
                    if len(c) > 0:
                        sp1 = float(c)
                    else: 
                        sp1 = 0
                    if sp1 < 11:  #Screen for junk sales
                        b = a.parent.find_next('tr').find_next('tr').get_text()
                        if b.count('\n') > 4:   #This line has sales dat
                            sd2 = b.split('\n')[1]
                            c = b.split('\n')[4].replace('$','').replace(',','').strip()
                            if len(c) > 0:
                                sp2 = float(c)
                            else:
                                sp2 = 0

            if sp1 == 0 and sp2 == 0:
                sale_price.append('NA')
                sale_date.append('NA')
            elif sp1 >= sp2:
                sale_price.append(sp1)
                sale_date.append(sd1)
            else:
                sale_price.append(sp2)
                sale_date.append(sd2)                    

            found_acres = False            
            for a in soup.find_all('div', text='2022'):
                b = a.parent.parent.get_text() # Year, Acre, lots, Land Asmt, #Bldg, Bldg Asmt, Tot Asmt, Rat CD, RC
                if b.count('\n') > 4:
                    found_acres = True
                    if len(b.split('\n')[2].strip()) > 0:
                        acres.append(b.split('\n')[2].strip())
                    else:
                        acres.append('NA')
                    if len(b.split('\n')[5].strip()) > 0:
                        bldgs.append(b.split('\n')[5].strip())
                    else:
                        bldgs.append('Land')
                    if len(b.split('\n')[4].strip()) > 0 and len(b.split('\n')[7].strip()) > 0:
                        landasmt.append(round(int(b.split('\n')[4].strip()) / int(b.split('\n')[7].strip()),2))
                    else:
                        landasmt.append('NA')
            if not found_acres:
                acres.append('NA')
                bldgs.append('NA')
                landasmt.append('NA')
                

            if len(phys_address) <= 1:
                dist.append('Not Found')
                address.append('NA')                    
            else:
                if mail_address == phys_address:
                    origin = phys_address + city + ',' + state
                else:    #Anderson hard coded as city
                    origin = phys_address + ' Anderson, SC'
                address.append(origin)
                if find_distance:
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
props['bldgs'] = bldgs
props['landasmt'] = landasmt

props.to_csv(filename.replace(".csv","_out.csv"), index = False)    
