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
    zone:
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

RETURN = '''
memset_api:
  description: Domain info from the Memset API
  returned: when state == present and Gcheck_mode
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
    msg, _stderr, _memset_api = None, None, None
    payload = dict()

    # get the zones and check if the relevant zone exists
    api_method = 'dns.zone_list'
    _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists = check_zone(data=response, name=args['zone'])
    if not zone_exists:
        has_failed = True
        _stderr = "DNS zone '{}' does not exist, cannot create domain." . format(args['zone'])
        module.fail_json(failed=has_failed, msg=_stderr, stderr=_stderr)

    if args['state'] == 'present':
        counter = 0
        for zone in response.json():
            if zone['nickname'] == args['zone']:
                zone_id = zone['id']
                counter += 1
        if counter == 1:
            api_method = 'dns.zone_domain_list'
            _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)
            for zone_domain in response.json():
                if zone_domain['domain'] == args['domain']:
                    has_changed = False
                    break
            else:
                api_method = 'dns.zone_domain_create'
                payload['domain'] = args['domain']
                payload['zone_id'] = zone_id
                has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True
                else:
                    msg = _msg
        else:
            has_failed = True
            _stderr = 'Multiple zones with the same name exist.'
            module.fail_json(failed=True, msg=_stderr, stderr=_stderr)
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
                _memset_api = response.json()

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed
    retvals['msg'] = msg
    if _memset_api is not None:
        retvals['memset_api'] = _memset_api

    return(retvals)

def main(args= dict()):
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
        _stderr = 'Zone domain must be less than 250 characters in length.'
        module.fail_json(failed=True, msg = _stderr, stderr=_stderr)

    if module.check_mode:
        retvals = check(args)
    else:
        retvals = create_or_delete_domain(args)

    if args['state'] == 'present' and not module.check_mode and retvals['changed'] and not retvals['failed']:
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
