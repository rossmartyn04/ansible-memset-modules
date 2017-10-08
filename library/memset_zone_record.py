#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.memset import check_zone
from ansible.module_utils.memset import memset_api_call
from ansible.module_utils.memset import get_zone_id
import ipaddress
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: memset_zone
author: "Simon Weald (@analbeard)"
version_added: "2.3"
short_description: Manage zones
notes:
  - Zones can be thought of as a logical group of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the 
    Memset customer control panel is needed with the following minimum scope:
    `dns.zone_create`, `dns.zone_delete`, `dns.zone_list`.
description:
    - Manage DNS zones. These form the basis of grouping similar domains together.
options:
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel
    name:
        required: true
        description:
            - The zone nickname; usually the same as the main domain. Ensure this 
              value has at most 250 characters.
    ttl:
        required: false
        description:
            - The default TTL for all records created in the zone. This must be a
              valid int from https://www.memset.com/apidocs/methods_dns.html#dns.zone_create
'''

EXAMPLES = '''
# Create the zone 'test'
- name: create zone
  local_action:
    module: memset_zone_record
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: absent
    zone: testzone
    type: A
    record: www
    address: 1.2.3.4
    ttl: 600
    relative: True
'''

RETURN = ''' # '''

# def check(opts):
#     has_failed, msg, zone_id = get_zone_id(opts)
#     if has_failed:
#         module.fail_json(failed=failed, msg=msg)

#     # get all domain records in the account
#     api_method = 'dns.zone_record_list'
#     has_changed, has_failed, msg, response = memset_api_call(api_key, api_method)

#     # loop over all records
#     for record in response.json():
#         # attempt to match zone, record and type to see if the record exists
#         if set([record['zone_id'], record['type'], record['record']]).issubset(set([zone_id, record_type, therecord])):
#             if opts['state'] == 'present':
#                 #check all fields to see if any changes would occur
#             elif opts['state'] == 'absent':
#                 record_exists = True
#                 break
#         else:
#             record_exists = False







#     try:
#         changed
#     except NameError:
#         changed = ( (record_exists and opts['state'] == 'absent') or (not record_exists and opts['state'] == 'present') )
#     else:
#         changed = changed

#     module.exit_json(changed=changed)



# # zone_id (simonweald.com): 4b15a2ca1f07c1bf6d41d378973867d8
# {
#     "priority": 0,
#     "zone_id": "8fe36eadce2410820842d00e2a45a755",
#     "address": "31.25.188.56",
#     "relative": false,
#     "record": "beta",
#     "ttl": 0,
#     "type": "A",
#     "id": "5e9be01e84b024b84196858972dcf0f5"
# },



    # zone_exists = check_zone(api_key=kwargs['api_key'], api_method=api_method, name=kwargs['name'], payload=kwargs['payload'])

    # set changed to true if the operation would cause a change    
    
def create_or_delete(**kwargs):
    has_failed = False
    has_changed = False
    msg = ''
    payload = kwargs['payload']
    api_method = 'dns.zone_list'

    zone_exists = check_zone(api_key=kwargs['api_key'], api_method=api_method, name=kwargs['name'])

    if kwargs['state'] == 'present':
        if zone_exists:
            # get a list of all zones and find the zone's ID
            _, _, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method)
            for zone in response.json():
                if zone['nickname'] == kwargs['name']:
                    break
            # get a list of all records (can't limit by zone) and iterate to find relevant record
            api_method = 'dns.zone_record_list'
            _, _, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method)
            
            # assemble our new record
            new_record = dict()
            new_record['zone_id'] == zone['id']
            new_record['priority'] == kwargs['priority']
            new_record['address'] == kwargs['address']
            new_record['relative'] == kwargs['relative']
            new_record['record'] == kwargs['record']
            new_record['ttl'] == kwargs['ttl']
            new_record['type'] == kwargs['type']

            # check if a matching record exists
            for record in response.json():
                if record['zone_id'] == zone['id'] and record['address'] == kwargs['address'] and record['record'] == kwargs['record'] and record['type'] == kwargs['type']:
                    # record exists, add ID to payload
                    new_record['id'] == record['id']
                    # check if existing record matches user-provided values
                    if record == new_record:
                        module.exit_json(changed=False, msg=msg)
                    else:
                        # merge dicts ensuring we change any updated values
                        payload = {**record, **new_record}
                        api_method = 'dns.zone_record_update'
                        break
                else:
                    # no record found, so we create it
                    api_method = 'dns.zone_record_create'
                    payload = new_record
                    break

            has_changed, has_failed, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
        else:
            has_failed = True
            msg = 'Zone must exist before records are created'

    if kwargs['state'] == 'absent':
        if zone_exists:
            _, _, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
            counter = 0
            for zone in response.json():
                if zone['nickname'] == kwargs['name']:
                    counter += 1
            if counter == 1:
                for zone in response.json():
                    if zone['nickname'] == kwargs['name']:
                        zone_id = zone['id']
                api_method = 'dns.zone_delete'
                payload['id'] = zone_id
                has_changed, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
            else:
                has_failed = True
                msg = 'Multiple zones with the same name exist.'
        else:
            has_failed = False
            
    if has_failed:
        module.fail_json(failed=True, msg=msg)

    if has_changed:
        module.exit_json(changed=True, msg=msg)
    else:
        module.exit_json(changed=False, msg=msg)

def main():
    global module
    module = AnsibleModule(
        argument_spec = dict(
            state       = dict(required=True, choices=[ 'present', 'absent' ], type='str'),
            api_key     = dict(required=True, type='str', no_log=True),
            zone        = dict(required=True, type='str'),
            record_type = dict(required=True, aliases=['type'], choices=[ 'A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT' ], type='str'),
            record      = dict(required=True, default='', type='str'),
            address     = dict(required=True, aliases=['ip'], type='str'),
            ttl         = dict(required=False, choices=[ 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400 ], type='int'),
            priority    = dict(required=False, type='int'),
            relative    = dict(required=False, type='bool')
        ),
        supports_check_mode=True
    )

    opts = dict()

    opts['payload']     = dict()
    opts['state']       = module.params['state']
    opts['api_key']     = module.params['api_key']
    opts['zone']        = module.params['zone']
    opts['record_type'] = module.params['record_type']
    opts['record']      = module.params['record']
    opts['address']     = module.params['address']
    try:
        module.params['ttl']
    except KeyError:
        opts['ttl'] = 0
    else:
        opts['ttl'] = module.params['ttl']
    try:
        module.params['priority']
    except KeyError:
        opts['priority'] = 0
    else:
        opts['priority'] = module.params['priority']
    try:
        module.params['relative']
    except KeyError:
        opts['relative'] = False
    else:
        opts['relative'] = module.params['relative']

    if opts['record_type'] in [ 'A', 'AAAA' ]:
        if not ipaddress.ip_address(opts['address']):
            module.fail_json(failed=True, msg='IP address is not valid.')
    if opts['priority']:
        if not 0 <= opts['priority'] <= 999:
            module.fail_json(failed=True, msg='Priority must be in the range 0 > 999 (inclusive).')

    if module.check_mode:
        check(opts)
    else:
        create_or_delete(opts)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':  
    main()
