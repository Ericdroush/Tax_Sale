# Tax_Sale
Program used to find tax sale properties, information about the properties, and screen them for desirable attributes.

#To run:
1. Clone repo
2. Set up a Google API account and get a key
   - The key needs to be stored in an environment variable called  
     "GOOGLE_API_KEY" (without the quotes)
3. Run main.py

# County Specific Steps
### Greenville
The list of properties will be pulled from the following website: http://www.greenvillecounty.org/appsAS400/Taxsale/  
It's possible that this site or the format change from year to year and might need some tweaking

### Anderson
There is no good way to automatically get the listing of properties.  You need to get the newspaper
add and save as a CSV file called "NewspaperAd.csv"
The website is ...

### Pickens
TBD

### Spartanburg
- Go to this website https://www.spartanburgcounty.org/640/2023-Tax-Sale-Info (Assume this link will be different every year)
- Click on Real Estate
- On the new webpage press Ctrl+A to select all and Ctrl+C to copy
- Paste in a text file called props_from_web.csv in this directory
- C:\Users\ericd\OneDrive\Documents\Python Scripts\Tax_Sale\Counties\Spartanburg

