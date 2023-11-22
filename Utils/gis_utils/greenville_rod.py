# https://www.zenrows.com/blog/scraping-javascript-rendered-web-pages#build-scraper-selenium

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By

# Define the Chrome webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless") # Set the Chrome webdriver to run in headless mode for scalability

# By default, Selenium waits for all resources to download before taking actions.
# However, we don't need it as the page is populated with dynamically generated JavaScript code.
options.page_load_strategy = "none"

# Pass the defined options objects to initialize the web driver
driver = Chrome(options=options)
# Set an implicit wait of 5 seconds to allow time for elements to appear before throwing an exception
driver.implicitly_wait(5)

url = "https://www.instacart.com/store/sprouts/collections/bread/872?guest=true"

driver.get(url)
#time.sleep(20)
