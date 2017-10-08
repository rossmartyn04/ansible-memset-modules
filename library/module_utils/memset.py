#!/usr/bin/env python

import requests

def memset_api_call(api_key, api_method, **kwargs):
    '''
    Generic function which returns results back to calling function.
    '''
    # if we've already started preloading the payload then use that
    try:
        kwargs['payload']
    except KeyError:
        payload = dict()
    else:
        payload = kwargs['payload']
    payload['api_key'] = api_key
    # set some sane defaults
    has_changed = False
    has_failed = False
    response = None
    api_uri_base = 'https://api.memset.com/v1/json/'
    api_uri = '{}{}/' . format(api_uri_base, api_method)

    try:
        response = requests.post(api_uri, data=payload)
    except Exception as e:
        has_failed = True
        msg = e
    else:
        has_changed = response.status_code in [201, 200]

    if response.status_code in [400, 403, 404]:
        has_failed = True

    del payload['api_key']

    msg = response.json()
    return(has_changed, has_failed, msg, response)

def check_zone_domain(**kwargs):
    '''
    Returns true if domain already exists, and false if not.
    '''
    api_method = 'dns.zone_domain_list'
    payload = kwargs['payload']

    _, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)

    if response.status_code in [201, 200]:
        for zone_domain in response.json():
            if zone_domain['domain'] == kwargs['domain']:
                return True
        else:
            return False

def check_zone(**kwargs):
    '''
    Returns true if zone already exists, and false if not.
    '''
    _, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=kwargs['api_method'])

    if response.status_code in [201, 200]:
        for zone in response.json():
            if zone['nickname'] == kwargs['name']:
                return True
        else:
            return False

def get_zone_id(opts):
    '''
    Returns the zone's id if it exists and is unique
    '''
    api_method = 'dns.zone_list'
    _, has_failed, msg, response = memset_api_call(api_key=opts['api_key'], api_method=api_method)

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
