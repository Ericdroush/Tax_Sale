# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 19:44:27 2022

1.  First clean property data by running prop_data_converter
2.  Download Pickens_Open_Data.csv from https://pcgis-pickenscosc.opendata.arcgis.com/
3.  Look up Columns of interest, must include Account No. 
4.  Save as props.csv
3.  Run this to find distance to Clemson, add Address, Tax Area

@author: ericd
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

find_distance = False

props = pd.read_csv('Properties_Clean.csv',names=['MapID','Owner','Amount'],skiprows = 1)
data = pd.read_csv('Pickens_Open_data.csv')

col_list = ['MapID', 
            'Owner',
            'Amount', 
            'Address', 
            'TaxID', 
            'Bldgs', 
            'Acres', 
            'CalcAcres', 
            'Account', 
            'Sale Date', 
            'Sale Price', 
            'Market Value',
            'Dist', 
            'County_Link', 
            'Maps_Link']

props2 = pd.DataFrame(columns = col_list)

if Path('props2.csv').is_file():
    props2_old = pd.read_csv('props2.csv', sep=',', dtype=str)    
    check_existing = True
else:
    props2.to_csv('props2.csv', index = False)   #Write out headers
    check_existing = False


for prop in props.MapID:
        
    if not check_existing or not (props2_old['MapID'].eq(prop)).any():

        df = data.loc[(data.PIN == prop)]   
        
        #Can also query https://services1.arcgis.com/59960rq18IxUcAVI/arcgis/rest/services/Pickens_Open_data/FeatureServer/6/query?where=PIN = '4037-00-34-7408'&outFields=*&outSR=4326&f=json
        #will provide the same data plus GPS coords
        
        
        #Initialize data, will get overwritten later with values if they exist
        address = 'NA'
        taxid = 'NA'
        lot = 'NA'
        acres = 'NA'
        calcacres = 'NA'
        account = 'NA'
        saledate = 'NA'
        saleprice = 'NA'
        market = 'NA'
        dist = 'NA'
        county_link = 'NA'
        maps_link = 'NA'
    
        if len(df) != 0:
        
            if len(df.LOCADD.iloc[0]) <2:
                address = df.ADD1.iloc[0] + ' ' + df.CITY.iloc[0] + ', ' + df.STATE.iloc[0]
            else: 
                address = df.LOCADD.iloc[0] + ' ' + df.LOCCITY.iloc[0] + ', SC'
            
            if len(df.TAXAREA.iloc[0]) != 0:
                taxid = df.TAXAREA.iloc[0]
            
            if len(str(df.BLDGS.iloc[0])) != 0 and df.BLDGS.iloc[0] > 0:
                lot = df.BLDGS.iloc[0]
            else:
                lot = 'Land'
            
            if len(str(df.ACRES.iloc[0])) != 0:
                acres = df.ACRES.iloc[0]
                
            if len(str(df.CalcAcres.iloc[0])) != 0:
                calcacres = df.CalcAcres.iloc[0]
    
            if len(df.ACCTNO.iloc[0]) != 0:
                account = df.ACCTNO.iloc[0]
            
            if len(str(df.SALEDT.iloc[0])) != 0:
                saledate = df.SALEDT.iloc[0]
            
            if len(str(df.SALEP.iloc[0])) != 0:
                saleprice = df.SALEP.iloc[0]
    
            if len(address) <= 3:   #Blank or NA
                dist = 'No Address'
            else:
                if find_distance:
                    print(prop)
                    origin = address
                    #dest = '34.677139,-82.836417'   #Location of Clemson - no spaces!
                    dest = '34.931775,-82.591247'   #Location on east side of county - for lake property screen
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
                    dist = 'NLU'
    
            if len(account) >= 8:
                county_link = '=HYPERLINK("https://qpublic.schneidercorp.com/Application.aspx?AppID=927&LayerID=18058&PageTypeID=1&PageID=8074&Q=798070542&KeyValue=' + prop + '","County")'

            if len(address) > 3:
                maps_link = '=HYPERLINK("https://www.google.com/maps/search/?api=1&query=' + address.replace('+','%2B').replace(' ','+') + '","Map")'
    
            if len(account) >= 8:
                url = 'https://qpublic.schneidercorp.com/Application.aspx?AppID=927&LayerID=18058&PageTypeID=4&PageID=8077&Q=810072412&KeyValue=' + account
                chrome_options = Options()
                #chrome_options.headless = True
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                #dr = webdriver.Chrome(options=options, executable_path=r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe')
                #dr = webdriver.Chrome()
                dr = webdriver.Chrome(options=chrome_options)
                dr.get(url)
                soup = BeautifulSoup(dr.page_source,"lxml")          

                print(soup)
                a = soup.find('th', text=re.compile('Market Value'))
                print(a)
                market = a.nextSibling.get_text().strip()
                print(market)

           
        data_list = [prop, 
                     props['Owner'].loc[(props.MapID == prop)], 
                     props['Amount'].loc[(props.MapID == prop)], 
                     address, 
                     taxid, 
                     lot, 
                     acres, 
                     calcacres, 
                     account, 
                     saledate, 
                     saleprice, 
                     market,
                     dist, 
                     county_link, 
                     maps_link]
        props2.loc[0] = data_list    
        props2.to_csv('props2.csv', mode='a', index=False, header=False)    





