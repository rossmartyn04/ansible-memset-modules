#!/usr/bin/env python

import requests

def memset_api_call(api_key, api_method, payload=None):
    '''
    Generic function which returns results back to calling function.

    Requires an API key and an API method to assemble the API URL.
    Returns response text to be analysed.
    '''
    # if we've already started preloading the payload then use that
    if payload is None:
        payload = dict()

    payload['api_key'] = api_key
    # set some sane defaults
    has_failed = False
    response, msg = None, None
    api_uri_base = 'https://api.memset.com/v1/json/'
    api_uri = '{}{}/' . format(api_uri_base, api_method)

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

def check_zone_domain(api_key, payload, domain):
    '''
    Returns true if domain already exists, and false if not.
    '''
    api_method = 'dns.zone_domain_list'

    has_failed, msg, response = memset_api_call(api_key=api_key, api_method=api_method, payload=payload)

    if response.status_code in [201, 200]:
        for zone_domain in response.json():
            if zone_domain['domain'] == domain:
                return True
        else:
            return False

def check_zone(data, name):
    '''
    Returns true if zone already exists, and false if not.
    '''
    if data.status_code in [201, 200]:
        for zone in data.json():
            if zone['nickname'] == name:
                return True
        else:
            return False

def get_zone_id(opts):
    '''
    Returns the zone's id if it exists and is unique
    '''
    api_method = 'dns.zone_list'
    has_failed, msg, response = memset_api_call(api_key=opts['api_key'], api_method=api_method)

    counter = 0
    failed = False
    zone_id = None
    if response.status_code in [201, 200]:
        for zone in response.json():
            if zone['nickname'] == opts['zone']:
                zone_id = zone['id']
                counter += 1
        if counter == 0:
            failed = True
            msg = 'No matching zone found.'
        if counter > 1:
            zone_id = None
            failed = True
            msg = 'Duplicate zones found.'
    else:
        failed = True
        msg = 'API returned an invalid status code.'

    return(failed, msg, zone_id)
