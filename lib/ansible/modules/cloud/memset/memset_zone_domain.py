#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.memset import get_zone_id
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
version_added: "2.5"
short_description: Manage zone domains
notes:
  - Zone domains can be thought of as a collection of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the
    Memset customer control panel is needed with the following minimum scope -
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
    zone:
        required: true
        description:
            - The zone to add the domain to (this must already exist)
'''

EXAMPLES = '''
# Create the zone domain 'test.com'
- name: create zone domain
  memset_zone_domain:
    domain: test.com
    zone: testzone
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
  delegate_to: localhost
'''

RETURN = '''
memset_api:
  description: Domain info from the Memset API
  returned: when changed or state == present
  type: complex
  contains:
    domain:
      description: Domain name
      returned: always
      type: string
      sample: "example.com"
    id:
      description: Domain ID
      returned: always
      type: string
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
'''


def check(args, retvals=dict()):
    api_method = 'dns.zone_domain_list'
    has_changed = False

    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    domain_exists = check_zone_domain(data=response, domain=args['domain'])

    # set changed to true if the operation would cause a change
    has_changed = ((domain_exists and args['state'] == 'absent') or (not domain_exists and args['state'] == 'present'))

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed

    return(retvals)


def create_or_delete_domain(args, retvals=dict()):
    has_changed, has_failed = False, False
    msg, stderr, memset_api = None, None, None
    payload = dict()

    # get the zones and check if the relevant zone exists
    api_method = 'dns.zone_list'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    if has_failed:
        retvals['failed'] = has_failed
        retvals['msg'] = msg
        retvals['stderr'] = "API returned an error: {}" .format(response.status_code)
        return(retvals)

    zone_exists, msg, counter, zone_id = get_zone_id(zone_name=args['zone'], current_zones=response.json())
    if not zone_exists:
        has_failed = True
        if counter == 0:
            stderr = "DNS zone '{}' does not exist, cannot create domain." . format(args['zone'])
        elif counter > 1:
            stderr = "{} matches multiple zones, cannot create domain." . format(args['zone'])

        retvals['failed'] = has_failed
        retvals['msg'] = stderr
        retvals['stderr'] = stderr
        return(retvals)

    if args['state'] == 'present':
        # making it this far means we have a unique zone to use
        api_method = 'dns.zone_domain_list'
        _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)
        for zone_domain in response.json():
            if zone_domain['domain'] == args['domain']:
                # zone domain already exists, nothing to change
                has_changed = False
                break
        else:
            # we need to create the domain
            api_method = 'dns.zone_domain_create'
            payload['domain'] = args['domain']
            payload['zone_id'] = zone_id
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True
    if args['state'] == 'absent':
        api_method = 'dns.zone_domain_list'
        _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)
        domain_exists = check_zone_domain(data=response, domain=args['domain'])
        if domain_exists:
            api_method = 'dns.zone_domain_delete'
            payload['domain'] = args['domain']
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True
                memset_api = response.json()
                msg = None

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed
    for val in ['msg', 'stderr', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main(args=dict()):
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            domain=dict(required=True, aliases=['name'], type='str'),
            zone=dict(required=True, type='str')
        ),
        supports_check_mode=True
    )

    args['state'] = module.params['state']
    args['api_key'] = module.params['api_key']
    args['domain'] = module.params['domain']
    args['zone'] = module.params['zone']

    # zone domain length must be less than 250 chars
    if len(args['domain']) > 250:
        stderr = 'Zone domain must be less than 250 characters in length.'
        module.fail_json(failed=True, msg=stderr, stderr=stderr)

    if module.check_mode:
        retvals = check(args)
    else:
        retvals = create_or_delete_domain(args)

    if not retvals['failed']:
        if args['state'] == 'present' and not module.check_mode:
            payload = dict()
            payload['domain'] = args['domain']
            api_method = 'dns.zone_domain_info'
            _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            retvals['memset_api'] = response.json()

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
