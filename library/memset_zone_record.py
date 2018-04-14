#!/usr/bin/python

# from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.memset import check_zone
from ansible.module_utils.memset import memset_api_call
from ansible.module_utils.memset import get_zone_id
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: memset_zone_record
author: "Simon Weald (@analbeard)"
version_added: "2.4"
short_description: Manage zone records
notes:
  - Zones can be thought of as a logical group of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the 
    Memset customer control panel is needed with the following minimum scope:
    `dns.zone_create`, `dns.zone_delete`, `dns.zone_list`.
description:
    - Manage individual zone records.
options:
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel
    data:
        required: true
        description:
            - The address for this record (can be IP or text string depending on record type)
    priority:
        required: false
        description;
            - SRV/TXT record priority, in the range 0 > 999 (inclusive)
    record:
        required: false
        description:
            - The subdomain to create
    record_type:
        required: true
        description:
            - The type of DNS record to create. Must be one of:
              'A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT'
    relative:
        required: false
        description:
            - If set then the current domain is added onto the address field for CNAME, MX, NS 
              and SRV record types.
    ttl:
        required: false
        description:
            - The record's TTL in seconds (will inherit zone's TTL if not explicitly set). 
              This must be one of: 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400
              (where 0 implies inheritance from the zone)
    zone:
        required: true
        description:
            - The name of the zone to add this record to
'''

EXAMPLES = '''
# Create DNS record for www.domain.com
- name: create DNS record
  local_action:
    module: memset_zone_record
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: present
    zone: domain.com
    type: A
    record: www
    data: 1.2.3.4
    ttl: 300
    relative: false

# create an SPF record for domain.com
- name: create SPF record for domain.com
  local_action:
    module: memset_zone_record
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: present
    zone: domain.com
    type: TXT
    data: "v=spf1 +a +mx +ip4:a1.2.3.4 ?all"
'''

RETURN = ''' # '''

def create_or_delete(args):
    has_failed = False
    has_changed = False
    msg = ''
    response = ''
    payload = args['payload']
    api_method = 'dns.zone_list'

    zone_exists = check_zone(api_key=args['api_key'], api_method=api_method, name=args['zone'])

    if zone_exists:
        # get a list of all zones and find the zone's ID
        _, _, zone_response = memset_api_call(api_key=args['api_key'], api_method=api_method)
        for zone in zone_response.json():
            if zone['nickname'] == args['zone']:
                break

        # get a list of all records ( as we can't limit records by zone)
        api_method = 'dns.zone_record_list'
        _, _, record_response = memset_api_call(api_key=args['api_key'], api_method=api_method)

        # find any matching records
        records = [record for record in record_response.json() if record['zone_id'] == zone['id'] and record['record'] == args['record'] and record['type'] == args['type']]

        if args['state'] == 'present':
            # assemble the new record
            new_record = dict()
            new_record['zone_id'] = zone['id']
            new_record['priority'] = args['priority']
            new_record['address'] = args['address']
            new_record['relative'] = args['relative']
            new_record['record'] = args['record']
            new_record['ttl'] = args['ttl']
            new_record['type'] = args['type']

            # if we have any matches, update them
            if records:
                for zone_record in records:
                    # record exists, add ID to payload
                    new_record['id'] = zone_record['id']
                    if zone_record == new_record:
                        has_changed = False
                    else:
                        # merge dicts ensuring we change any updated values
                        payload = zone_record.copy()
                        payload.update(new_record)
                        api_method = 'dns.zone_record_update'
                        if args['check_mode']:
                            has_changed = True
                            return(has_changed, has_failed, msg, response)
                        has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                        if not has_failed:
                            has_changed = True
            else:
                # no record found, so we need to create it
                api_method = 'dns.zone_record_create'
                payload = new_record
                if args['check_mode']:
                    has_changed = True
                    return(has_changed, has_failed, msg, response)
                has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True

        if args['state'] == 'absent':
            # if we have any matches, delete them
            if records:
                for zone_record in records:
                    if args['check_mode']:
                        has_changed = True
                        return(has_changed, has_failed, msg, response)
                    payload['id'] = zone_record['id']
                    api_method = 'dns.zone_record_delete'
                    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                    if not has_failed:
                        has_changed = True
    else:
        if args['state'] == 'present':
            has_failed = True
            msg = 'Zone must exist before records are created'
        if args['state'] == 'absent':
            has_changed = False

    return(has_changed, has_failed, msg, response)


def main(args=dict()):
    global module
    module = AnsibleModule(
        argument_spec = dict(
            state    = dict(required=True, choices=[ 'present', 'absent' ], type='str'),
            api_key  = dict(required=True, type='str', no_log=True),
            zone     = dict(required=True, type='str'),
            type     = dict(required=True, aliases=['type'], choices=[ 'A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT' ], type='str'),
            data     = dict(required=True, aliases=['ip'], type='str'),
            record   = dict(required=False, default='', type='str'),
            ttl      = dict(required=False, default=0, choices=[ 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400 ], type='int'),
            priority = dict(required=False, default=0, type='int'),
            relative = dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    args['payload']     = dict()
    args['state']       = module.params['state']
    args['api_key']     = module.params['api_key']
    args['zone']        = module.params['zone']
    args['type']        = module.params['type']
    args['record']      = module.params['record']
    args['address']     = module.params['data']
    args['priority']    = module.params['priority']
    args['relative']    = module.params['relative']
    args['ttl']         = module.params['ttl']
    args['check_mode']  = module.check_mode
    # if args['type'] in [ 'A', 'AAAA' ]:
    #     if not ipaddress.ip_address(args['address']):
    #         module.fail_json(failed=True, msg='IP address is not valid.')
    if args['priority']:
        if not 0 <= args['priority'] <= 999:
            module.fail_json(failed=True, msg='Priority must be in the range 0 > 999 (inclusive).')

    has_changed, has_failed, msg, response = create_or_delete(args)

    if has_failed:
        module.fail_json(failed=has_failed, msg=msg)
    else:
        module.exit_json(changed=has_changed, msg=msg)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':  
    main()
