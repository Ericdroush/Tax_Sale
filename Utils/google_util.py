import requests
import json
import os

# Google API Key
googleapi = 'https://maps.googleapis.com/maps/api/'


def run_google_api(api_name, params):

    if "GOOGLE_API_KEY" not in os.environ:
        print('You need to create a Google API and place the key in an environment variable \n')
        print('called "GOOGLE_API_KEY" \n')
    params['key'] = os.environ["GOOGLE_API_KEY"]
    response = requests.get(googleapi + api_name + '/json?', params)

    # print(response.text)
    return json.loads(response.text)


def reverse_geo(lat, lon):

    params = {'latlng': str(lat) + ',' + str(lon)}

    output = run_google_api('geocode', params)
    if output['status'] == 'OK':
        add1 = output['plus_code']['compound_code']  # Actual center of property
        # add2 = output['results'][0]['formatted_address']  #Closest actual address - could be misleading
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
                    # Convert meters to miles
                    dist.append(round(output['rows'][0]['elements'][i]['distance']['value'] / 1609, 1))
                except:
                    dist.append('Failed')
            else:
                dist.append('NaN')
    else:
        dist.append('Failed')

    return dist


def get_streetview(taxmap, county, loc):
    from PIL import Image
    import io

    params = {
        'location': loc,
        'size': '600x400',
        'fov': 55
    }
    api_name = 'streetview'
    # output = run_google_api('streetview', params)
    params['key'] = os.environ["GOOGLE_API_KEY"]
    response = requests.get(googleapi + api_name + '?', params)

    with open('../Counties/' + county + '/StreetView/' + taxmap + '.jpg', "wb") as file:
        file.write(response.content)

    img = Image.open(io.BytesIO(response.content))
    img.show()

    return


def get_mapview(taxmap, county, loc):
    from PIL import Image
    import io

    params = {
        'center': loc,
        'zoom': 20,
        'size': '600x400',
        'format': 'jpg',
        'scale': 1,
        'maptype': 'satellite'
    }
    api_name = 'staticmap'
    # output = run_google_api('streetview', params)
    params['key'] = os.environ["GOOGLE_API_KEY"]
    response = requests.get(googleapi + api_name + '?', params)

    with open('../Counties/' + county + '/MapView/' + taxmap + '.jpg', "wb") as file:
        file.write(response.content)

    img = Image.open(io.BytesIO(response.content))
    img.show()
    return

def get_county_view():
    pass
    return


# get_streetview('10101011','greenville', '205 Ford Circle Greer, SC')
# get_mapview('10101010','greenville', '106 Ford Circle Greer, SC')

