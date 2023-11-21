
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import json
import sys
import pandas as pd
from bs4 import BeautifulSoup


# adding utils to the system path
sys.path.insert(0, 'C:/Users/ericd/OneDrive/Documents/Python Scripts/Tax_Sale/Utils')
from tax_util import *

tm = '5-14-07-014.00'
#tm = '5-14-07-009.00'

params = {
    'AppID': '857',
    'LayerID': '16069',
    'PageTypeID': '4',
    'PageID': '7149',
    'Q': '1612596104',
    'KeyValue': tm

}

# cookies = {'ASP.NET_SessionId': 'onrqnlsnv0nydxcel4gm10rp'}
# cookies = {
#     '_ga':'GA1.1.1982219787.1694036943',
#     'ASP.NET_SessionId': 'vaug4zbrqgbvyjpe2jno3gbr',
#     '_ga_7ZQ1FTE1SG': 'GS1.1.1697997301.7.0.1697997301.0.0.0',
#     'cf_clearance': 'QDDFY34NGgfae5VC_Gr6scMY1NcY0Ngf8CYW_TVa0UA-1697997301-0-1-681ee7b0.d0076260.f1306b6a-0.2.1697997301'
# }

url = 'https://beacon.schneidercorp.com/Application.aspx?'

retries = Retry(
    total=3,
    backoff_factor=0.1,
    status_forcelist=[408, 429, 500, 502, 503, 504],
)
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=retries))
response = session.get(url, params=params) #, cookies=cookies)

soup = BeautifulSoup(response.content, 'html.parser')
print(soup)






