#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.memset import check_zone_domain
from ansible.module_utils.memset import memset_api_call
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: memset_zone_domain
author: "Simon Weald (@analbeard)"
version_added: "2.3"
short_description: Manage zone domains
notes:
  - Zone domains can be thought of as a collection of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the 
    Memset customer control panel is needed with the following minimum scope:
    `dns.zone_domain_create`, `dns.zone_domain_delete`, `dns.zone_domain_list`.
description:
    - Manage DNS zone domains. These form the basis of grouping similar domains together.
options:
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel
    domain:
        required: true
        aliases: ['name']
        description:
            - The zone domain name. Ensure this value has at most 250 characters.
    zone_name:
        required: true
        description:
            - The zone to add the domain to (this must already exist)
'''

EXAMPLES = '''
# Create the zone domain 'test.com'
- name: create zone domain
  local_action: 
    module: memset_zone_domain
    domain: test.com
    zone: testzone
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
'''

RETURN = ''' # '''

def check(**kwargs):
    changed = False
    api_method = 'dns.zone_domain_list'

    zone_exists = check_zone_domain(api_key=kwargs['api_key'], api_method=api_method, payload=kwargs['payload'], domain=kwargs['domain'])

    # set changed to true if the operation would cause a change    
    changed = ( (zone_exists and kwargs['state'] == 'absent') or (not zone_exists and kwargs['state'] == 'present') )

    module.exit_json(changed=changed)

def create_or_delete_domain(**kwargs):
    has_changed = False
    has_failed = False
    msg = None
    payload = kwargs['payload']

    if kwargs['state'] == 'present':
        if kwargs['zone_name'] is None:
            msg = 'A zone is needed to add the domain to.'
            module.fail_json(failed=True, msg=msg)
        api_method = 'dns.zone_list'
        _, _, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
        counter = 0
        for zone in response.json():
            if zone['nickname'] == kwargs['zone_name']:
                zone_id = zone['id']
                counter += 1
        if counter == 1:
            api_method = 'dns.zone_domain_list'
            _, _, _, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
            for zone_domain in response.json():
                if zone_domain['domain'] == kwargs['domain']:
                    has_changed = False
                    break
            else:
                api_method = 'dns.zone_domain_create'
                payload['domain'] = kwargs['domain']
                payload['zone_id'] = zone_id
                has_changed, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)
        else:
            has_failed = True
            msg = 'Multiple zones with the same name exist.'
    if kwargs['state'] == 'absent':
        api_method = 'dns.zone_domain_delete'
        payload['domain'] = kwargs['domain']
        has_changed, has_failed, msg, response = memset_api_call(api_key=kwargs['api_key'], api_method=api_method, payload=payload)

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
            state     = dict(required=False, default='present', choices=[ 'present', 'absent' ], type='str'),
            api_key   = dict(required=True, type='str', no_log=True),
            domain    = dict(required=True, aliases=['name'], type='str'),
            zone_name = dict(required=True, aliases=['zone'], type='str')
        ),
        supports_check_mode=True
    )
    
    payload   = dict()
    state     = module.params['state']
    api_key   = module.params['api_key']
    domain    = module.params['domain']
    zone_name = module.params['zone_name']
    # try:
    #     module.params['zone']
    # except NameError:
    #     zone_name = None
    # else:
    #     zone_name = module.params['zone']
    
    # zone domain length must be less than 250 chars
    if len(domain) > 250:
        module.fail_json(failed=True, msg="Zone domain must be less than 250 characters in length.")

    if module.check_mode:
        check(state=state, api_key=api_key, domain=domain, payload=payload)
    else:
        create_or_delete_domain(state=state, api_key=api_key, domain=domain, zone_name=zone_name, payload=payload)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':  
    main()
