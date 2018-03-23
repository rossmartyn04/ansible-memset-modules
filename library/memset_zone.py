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
            - Forces deletion of a zone and all zone domains/zone records it containsn.
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

def check(**kwargs):
    changed = False
    api_method = 'dns.zone_list'

    zone_exists = check_zone(api_key=kwargs['api_key'], api_method=api_method, name=kwargs['name'], payload=kwargs['payload'])

    # set changed to true if the operation would cause a change    
    changed = ( (zone_exists and kwargs['state'] == 'absent') or (not zone_exists and kwargs['state'] == 'present') )

    module.exit_json(changed=changed)

def create_or_delete(**kwargs):
    has_failed = False
    has_changed = False
    msg = ''
    payload = kwargs['payload']
    api_method = 'dns.zone_list'

    zone_exists = check_zone(api_key=kwargs['api_key'], api_method=api_method, name=kwargs['name'], payload=kwargs['payload'])

    if kwargs['state'] == 'present':
        if not zone_exists:
            api_method = 'dns.zone_create'
            payload['ttl'] = kwargs['ttl']
            payload['nickname'] = kwargs['name']
            has_changed, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
        else:
            _, _, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
            for zone in response.json():
                if zone['nickname'] == kwargs['name']:
                    break
            if zone['ttl'] != kwargs['ttl']:
                payload['id'] = zone['id']
                payload['ttl'] = kwargs['ttl']
                api_method = 'dns.zone_update'
                has_changed, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
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
                        domain_count = len(zone['domains'])
                        record_count = len(zone['records'])
                if (domain_count > 0 or record_count > 0) and kwargs['force'] == False: 
                    msg = 'Zone contains domains or records and force was not used.'
                    module.fail_json(failed=True, msg=msg, rc=2)
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
            state   = dict(required=True, choices=[ 'present', 'absent' ], type='str'),
            api_key = dict(required=True, type='str', no_log=True),
            name    = dict(required=True, aliases=['nickname'], type='str'),
            ttl     = dict(required=False, default=0, type='int'),
            force   = dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    state    = module.params['state']
    api_key  = module.params['api_key']
    name     = module.params['name']
    ttl      = module.params['ttl']
    force    = module.params['force']
    payload  = dict()

    # zone nickname length must be less than 250 chars
    if len(name) > 250:
        module.fail_json(failed=True, msg="Zone name must be less than 250 characters in length.")
    if ttl not in [ 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400 ]:
        module.fail_json(failed=True, msg="TTL is not an accepted duration.")

    if module.check_mode:
        check(state=state, api_key=api_key, name=name, payload=payload)
    else:
        create_or_delete(state=state, api_key=api_key, name=name, ttl=ttl, force=force, payload=payload)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':  
    main()
