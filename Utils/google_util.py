import requests
import json
from Utils.key import key

# Google API Key
googleapi = 'https://maps.googleapis.com/maps/api/'


def run_google_api(api_name, params):

    params['key'] = key()
    response = requests.get(googleapi + api_name + '/json?', params)

    # print(response.text)
    return json.loads(response.text)

def reversegeo(lat, lon):

    params = {'latlng': str(lat) + ',' + str(lon)}

    output = run_google_api('geocode', params)
    if output['status'] == 'OK':
        add1 = output['plus_code']['compound_code']  # Actual center of property
        # add2 = output['results'][0]['formatted_address']  #Closest actual address - could be misleading, for reference
    else:
        add1 = 'Failed'
    return add1

def geocode(address):

    params = {'address': address}

    output = run_google_api('geocode', params)

    if output['status'] == 'OK':
        lat = output['results'][0]['geometry']['location']['lat']
        lon = output['results'][0]['geometry']['location']['lng']
    else:
        lat = lon = 'Failed'
    return [lat, lon]

def find_distance(origin, destinations):

    # This function will get called with between 1 and 3 destinations
    # Return three distances, if less than 3 destinations were called, then return NaN for the those
    # Return Failed if something went wrong

    dest_count = 0
    new_dest = []
    for dest in destinations:
        if len(dest) > 0:
            dest_count += 1
            new_dest.append(dest)

    destinations = '|'.join([dest for dest in new_dest])

    params = {
        'origins': origin,
        'destinations': destinations,
        'units': 'imperial'
    }

    output = run_google_api('distancematrix', params)

    dist = []
    if output['status'] == 'OK':
        for i in range(3):
            if i <= dest_count - 1:
                try:
                    dist.append(round(output['rows'][0]['elements'][i]['distance']['value'] / 1609, 1))  # Convert meters to miles
                except:
                    dist.append('Failed')
                    print(output)
            else:
                dist.append('NaN')
    else:
        dist.append('Failed')

    return dist

