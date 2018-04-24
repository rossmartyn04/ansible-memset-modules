#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.memset import check_zone
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


def check(args):
    api_method = 'dns.zone_domain_list'

    _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=['payload'])

    zone_exists = check_zone_domain(data=response, domain=args['domain'])

    # set changed to true if the operation would cause a change
    has_changed = ((zone_exists and args['state'] == 'absent') or (not zone_exists and args['state'] == 'present'))

    module.exit_json(changed=has_changed)


def create_or_delete_domain(args):
    has_changed = False
    has_failed = False
    msg, _stderr = None
    payload = args['payload']

    # get the zones and check if the relevant zone exists
    api_method = 'dns.zone_list'
    _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists = check_zone(data=response, name=args['zone_name'])

    if args['state'] == 'present':
        if args['zone_name'] is None:
            _stderr = 'A zone is needed to add the domain to.'
            module.fail_json(failed=True, stderr=_stderr)
        api_method = 'dns.zone_list'
        _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        counter = 0
        for zone in response.json():
            if zone['nickname'] == args['zone_name']:
                zone_id = zone['id']
                counter += 1
        if counter == 1:
            api_method = 'dns.zone_domain_list'
            _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            for zone_domain in response.json():
                if zone_domain['domain'] == args['domain']:
                    has_changed = False
                    break
            else:
                api_method = 'dns.zone_domain_create'
                payload['domain'] = args['domain']
                payload['zone_id'] = zone_id
                has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True
        else:
            has_failed = True
            _stderr = 'Multiple zones with the same name exist.'
            module.fail_json(failed=True, stderr=_stderr)
    if args['state'] == 'absent':
        if zone_exists:
            api_method = 'dns.zone_domain_delete'
            payload['domain'] = args['domain']
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True

    if has_failed:
        module.fail_json(failed=True, msg=msg)

    if has_changed:
        module.exit_json(changed=True, msg=msg)
    else:
        module.exit_json(changed=False, msg=msg)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            domain=dict(required=True, aliases=['name'], type='str'),
            zone_name=dict(required=True, aliases=['zone'], type='str')
        ),
        supports_check_mode=True
    )

    args = dict()
    args['payload'] = dict()
    args['state'] = module.params['state']
    args['api_key'] = module.params['api_key']
    args['domain'] = module.params['domain']
    args['zone_name'] = module.params['zone_name']

    # zone domain length must be less than 250 chars
    if len(args['domain']) > 250:
        module.fail_json(failed=True, stderr="Zone domain must be less than 250 characters in length.")

    if module.check_mode:
        check(args)
    else:
        create_or_delete_domain(args)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
