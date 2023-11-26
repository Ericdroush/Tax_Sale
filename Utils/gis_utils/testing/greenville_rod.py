# https://www.zenrows.com/blog/scraping-javascript-rendered-web-pages#build-scraper-selenium

from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
import math

def pull_data(driver, xpath):
    try:
        out = driver.find_element(By.XPATH, xpath).get_attribute(
            "textContent").replace('$', '').replace(',', '').strip()
    except:
        out = 'NaN'

    return out


# Define the Chrome webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless") # Set the Chrome webdriver to run in headless mode for scalability
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
options.add_argument(f'user-agent={user_agent}')

# By default, Selenium waits for all resources to download before taking actions.
# However, we don't need it as the page is populated with dynamically generated JavaScript code.
# options.page_load_strategy = "none"

# Pass the defined options objects to initialize the web driver
driver = Chrome(options=options)
# Set an implicit wait of 5 seconds to allow time for elements to appear before throwing an exception
driver.implicitly_wait(5)

url = 'https://qpublic.schneidercorp.com/Application.aspx?AppID=857&LayerID=16069&PageTypeID=4&PageID=7149&Q=692867197&KeyValue='
tm1 = '5-14-07-014.00'  # Test Prop1
tm2 = '7-12-11-119.00'  # Church
tm3 = '7-12-11-113.00'  # Test Prop2

url = url + tm2

driver.get(url)

address = pull_data(driver, '//*[@id="ctlBodyPane_ctl00_ctl01_dynamicSummary_rptrDynamicColumns_ctl07_pnlSingleValue"]')
sq_ft = float(pull_data(driver, '//*[@id="ctlBodyPane_ctl06_ctl01_frmView_ctl00_lblFinishedSqFt"]')) # Residential properties
if math.isnan(sq_ft):
    sq_ft = float(pull_data(driver, '//*[@id="ctlBodyPane_ctl07_ctl01_frmView_ctl00_lblFinishedSqFt"]')) # Commercial properties

condition = pull_data(driver, '//*[@id="ctlBodyPane_ctl06_ctl01_frmView_ctl00_lblCondition"]')
if condition == 'NaN':
    condition = pull_data(driver, '//*[@id="ctlBodyPane_ctl07_ctl01_frmView_ctl00_lblCondition"]')

bldg_type = pull_data(driver,'//*[@id="ctlBodyPane_ctl00_ctl01_dynamicSummary_rptrDynamicColumns_ctl10_pnlSingleValue"]')
if '(' in bldg_type and ')' in bldg_type:
    land_use = bldg_type[bldg_type.find(start:='(')+len(start):bldg_type.find(')')]
else:
    land_use = 'NaN'
bldgs = pull_data(driver, '//*[@id="ctlBodyPane_ctl04_ctl01_gvwFees"]/tbody/tr/td[1]')
sd0 = pull_data(driver, '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[1]/th')
sp0 = float(pull_data(driver,  '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[1]/td[1]'))
sd1 = pull_data(driver,  '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[2]/th')
sp1 = float(pull_data(driver,  '//*[@id="ctlBodyPane_ctl10_ctl01_gvwList"]/tbody/tr[2]/td[1]'))
appraised_land = float(pull_data(driver,  '//*[@id="ctlBodyPane_ctl03_ctl01_grdValuation"]/tbody/tr[1]/td[2]'))
appraised_bldg = float(pull_data(driver,  '//*[@id="ctlBodyPane_ctl03_ctl01_grdValuation"]/tbody/tr[2]/td[2]'))
appraised_total = appraised_land + appraised_bldg

print('\n'.join([address, str(sq_ft), condition, bldgs, land_use, bldg_type, sd0,  str(sp0), sd1, str(sp1), str(appraised_land), str(appraised_bldg), str(appraised_total)]))
