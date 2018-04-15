#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.memset import check_zone
from ansible.module_utils.memset import memset_api_call
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
    force:
        required: false
        description:
            - Forces deletion of a zone and all zone domains/zone records it contains.
'''

EXAMPLES = '''
# Create the zone 'test'
- name: create zone
  local_action:
    module: memset_zone
    name: test
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
    ttl: 300

# Force zone deletion
- name: force delete zone
  local_action:
    module: memset_zone
    name: test
    state: absent
    api_key: 5eb86c9196ab03919abcf03857163741
    force: true
'''

RETURN = ''' # '''

def check(args):
    has_changed = False

    # get the zones and check if the relevant zone exists
    api_method = 'dns.zone_list'
    _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists = check_zone(data=response, name=args['name'])

    # set changed to true if the operation would cause a change    
    has_changed = ( (zone_exists and args['state'] == 'absent') or (not zone_exists and args['state'] == 'present') )

    module.exit_json(changed=has_changed)

def create_or_delete(args):
    has_failed = False
    has_changed = False
    msg = ''
    payload = args['payload']

    # get the zones and check if the relevant zone exists
    api_method = 'dns.zone_list'
    _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists = check_zone(data=response, name=args['name'])

    if args['state'] == 'present':
        if not zone_exists:
            api_method = 'dns.zone_create'
            payload['ttl'] = args['ttl']
            payload['nickname'] = args['name']
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True
        else:
            _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            for zone in response.json():
                if zone['nickname'] == args['name']:
                    break
            if zone['ttl'] != args['ttl']:
                payload['id'] = zone['id']
                payload['ttl'] = args['ttl']
                api_method = 'dns.zone_update'
                has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True
    if args['state'] == 'absent':
        if zone_exists:
            _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            counter = 0
            for zone in response.json():
                if zone['nickname'] == args['name']:
                    counter += 1
            if counter == 1:
                for zone in response.json():
                    if zone['nickname'] == args['name']:
                        zone_id = zone['id']
                        domain_count = len(zone['domains'])
                        record_count = len(zone['records'])
                if (domain_count > 0 or record_count > 0) and args['force'] == False:
                    msg = 'Zone contains domains or records and force was not used.'
                    has_failed, has_changed = True, False
                    module.fail_json(failed=has_failed, changed=has_changed, msg=msg, rc=1)
                api_method = 'dns.zone_delete'
                payload['id'] = zone_id
                has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True
            else:
                has_failed, has_changed = True, False
                msg = 'Multiple zones with the same name exist.'
        else:
            has_failed, has_changed = False, False

    if has_failed:
        module.fail_json(failed=has_failed, msg=msg)
    else:
        module.exit_json(changed=has_changed, msg=msg)

def main(args=dict()):
    global module
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(required=True, choices=[ 'present', 'absent' ], type='str'),
            api_key = dict(required=True, type='str', no_log=True),
            name    = dict(required=True, aliases=['nickname'], type='str'),
            ttl     = dict(required=False, default=0, type='int'),
            force   = dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    args['state']   = module.params['state']
    args['api_key'] = module.params['api_key']
    args['name']    = module.params['name']
    args['ttl']     = module.params['ttl']
    args['force']   = module.params['force']
    args['payload'] = dict()

    has_failed = False

    # zone nickname length must be less than 250 chars
    if len(args['name']) > 250:
        has_failed = True
        msg = "Zone name must be less than 250 characters in length."
    if args['ttl'] not in [ 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400 ]:
        has_failed = True
        msg = "TTL is not an accepted duration"
        
    if has_failed:
        module.fail_json(failed=has_failed, msg=msg)

    if module.check_mode:
        check(args)
    else:
        create_or_delete(args)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':  
    main()
