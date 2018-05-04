#!/usr/bin/env python

try:
    import requests
    requests_found = True
except ImportError:
    requests_found = False


def memset_api_call(api_key, api_method, payload=None):
    '''
    Generic function which returns results back to calling function.

    Requires an API key and an API method to assemble the API URL.
    Returns response text to be analysed.
    '''
    # if we've already started preloading the payload then copy it
    # and use that, otherwise we need to isntantiate it.
    if payload is None:
        payload = dict()
    else:
        payload = payload.copy()

    payload['api_key'] = api_key
    # set some sane defaults
    has_failed = False
    response, msg = None, None
    api_uri_base = 'https://api.memset.com/v1/json/'
    api_uri = '{0}{1}/' . format(api_uri_base, api_method)

    # make the request and capture any error to be returned
    # in the correct Ansible way.
    try:
        response = requests.post(api_uri, data=payload)
    except Exception as e:
        has_failed = True
        msg = e
    else:
        if response.status_code in [400, 403, 404, 412]:
            # the human made an error
            has_failed = True
        elif response.status_code in [500, 503]:
            # Memset's API isn't happy
            has_failed = True
            msg = "Internal server error"
        elif response.status_code in [201, 200]:
            pass

    del payload['api_key']

    if msg is None:
        msg = response.json()

    return(has_failed, msg, response)


def check_zone_domain(data, domain):
    '''
    Returns true if domain already exists, and false if not.
    '''
    exists = False

    if data.status_code in [201, 200]:
        for zone_domain in data.json():
            if zone_domain['domain'] == domain:
                exists = True

    return(exists)


def check_zone(data, name):
    '''
    Returns true if zone already exists, and false if not.
    '''
    counter = 0
    exists = False

    if data.status_code in [201, 200]:
        for zone in data.json():
            if zone['nickname'] == name:
                counter += 1
        if counter == 1:
            exists = True

    return(exists, counter)


def get_zone_id(zone_name, current_zones):
    '''
    Returns the zone's id if it exists and is unique
    '''
    zone_exists = False
    zone_id, msg = None, None
    zone_list = []

    for zone in current_zones:
        if zone['nickname'] == zone_name:
            zone_list.append(zone['id'])

    counter = len(zone_list)

    if counter == 0:
        msg = 'No matching zone found'
    elif counter == 1:
        zone_id = zone_list[0]
        zone_exists = True
    elif counter > 1:
        zone_id = None
        msg = 'Zone ID could not be returned as duplicate zone names were detected'

    return(zone_exists, msg, counter, zone_id)
