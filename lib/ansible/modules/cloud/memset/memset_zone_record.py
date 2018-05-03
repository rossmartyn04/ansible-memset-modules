#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Simon Weald <ansible@simonweald.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: memset_zone_record
author: "Simon Weald (@analbeard)"
version_added: "2.6"
short_description: Manage zone records
notes:
  - Zones can be thought of as a logical group of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the
    Memset customer control panel is needed with the following minimum scope -
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
        description:
            - SRV/TXT record priority, in the range 0 > 999 (inclusive)
    record:
        required: false
        description:
            - The subdomain to create
    record_type:
        required: true
        description:
            - The type of DNS record to create. Must be one of -
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
              This must be one of - 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400
              (where 0 implies inheritance from the zone)
    zone:
        required: true
        description:
            - The name of the zone to add this record to
'''

EXAMPLES = '''
# Create DNS record for www.domain.com
- name: create DNS record
  memset_zone_record:
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: present
    zone: domain.com
    type: A
    record: www
    data: 1.2.3.4
    ttl: 300
    relative: false
  delegate_to: localhost

# create an SPF record for domain.com
- name: create SPF record for domain.com
  memset_zone_record:
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: present
    zone: domain.com
    type: TXT
    data: "v=spf1 +a +mx +ip4:a1.2.3.4 ?all"
  delegate_to: localhost
'''

RETURN = '''
memset_api:
  description: Record info from the Memset API
  returned: when state == present
  type: complex
  contains:
    address:
      description: Record content (may be an IP, string or blank depending on record type)
      returned: always
      type: string
      sample: 1.1.1.1
    id:
      description: Record ID
      returned: always
      type: string
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
    priority:
      description: Priority for MX and SRV records
      returned: always
      type: integer
      sample: 10
    record:
      description: Name of record
      returned: always
      type: string
      sample: "www"
    relative:
      description: Adds the current domain onto the address field for CNAME, MX, NS and SRV types
      returned: always
      type: boolean
      sample: False
    ttl:
      description: Record TTL
      returned: always
      type: integer
      sample: 10
    type:
      description: Record type
      returned: always
      type: string
      sample: AAAA
    zone_id:
      description: Zone ID
      returned: always
      type: string
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
'''

from ansible.module_utils.memset import get_zone_id
from ansible.module_utils.memset import memset_api_call
from ansible.module_utils.memset import get_zone_id


def create_or_delete(args=None):
    has_failed, has_changed = False, False
    msg, memset_api, stderr = None, None, None
    payload = dict()
    retvals = dict()

    # get the zones and check if the relevant zone exists
    api_method = 'dns.zone_list'
    _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists, _, counter, zone_id = get_zone_id(zone_name=args['zone'], current_zones=response.json())

    if not zone_exists:
        has_failed = True
        if counter == 0:
            stderr = "DNS zone '{0}' does not exist." . format(args['zone'])
        elif counter > 1:
            stderr = "{0} matches multiple zones." . format(args['zone'])
        retvals['failed'] = has_failed
        retvals['msg'] = stderr
        retvals['stderr'] = stderr
        return(retvals)
    else:
        # we already have the zone's ID from above
        # get a list of all zones and find the zone's ID
        # _, _, zone_response = memset_api_call(api_key=args['api_key'], api_method=api_method)
        # for zone in zone_response.json():
        #     if zone['nickname'] == args['zone']:
        #         break

        # get a list of all records ( as we can't limit records by zone)
        api_method = 'dns.zone_record_list'
        _, _, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

        # find any matching records
        records = [record for record in response.json() if record['zone_id'] == zone_id
                   and record['record'] == args['record'] and record['type'] == args['type']]

        if args['state'] == 'present':
            # assemble the new record
            new_record = dict()
            new_record['zone_id'] = zone_id
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
                        # nothing to do; record is already correct
                        retvals['changed'] = has_changed
                        retvals['failed'] = has_failed
                        retvals['memset_api'] = zone_record
                        return(retvals)
                    else:
                        # merge dicts ensuring we change any updated values
                        payload = zone_record.copy()
                        payload.update(new_record)
                        api_method = 'dns.zone_record_update'
                        if args['check_mode']:
                            retvals['changed'] = True
                            # return the new record
                            retvals['memset_api'] = new_record
                            return(retvals)
                        has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                        if not has_failed:
                            has_changed = True
                            memset_api = new_record
                            # empty msg as we don't want to return a boatload of json to the user
                            msg = None
            else:
                # no record found, so we need to create it
                api_method = 'dns.zone_record_create'
                payload = new_record
                if args['check_mode']:
                    retvals['changed'] = True
                    retvals['failed'] = has_failed
                    retvals['memset_api'] = new_record
                    return(retvals)
                has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True
                    memset_api = new_record
                    #  empty msg as we don't want to return a boatload of json to the user
                    msg = None

        if args['state'] == 'absent':
            # if we have any matches, delete them
            if records:
                for zone_record in records:
                    if args['check_mode']:
                        retvals['changed'] = True
                        return(retvals)
                    payload['id'] = zone_record['id']
                    api_method = 'dns.zone_record_delete'
                    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                    if not has_failed:
                        has_changed = True
                        memset_api = zone_record
                        #  empty msg as we don't want to return a boatload of json to the user
                        msg = None

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed
    for val in ['msg', 'stderr', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            zone=dict(required=True, type='str'),
            type=dict(required=True, choices=['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT'], type='str'),
            address=dict(required=True, aliases=['ip', 'data'], type='str'),
            record=dict(required=False, default='', type='str'),
            ttl=dict(required=False, default=0, choices=[0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400], type='int'),
            priority=dict(required=False, default=0, type='int'),
            relative=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    args = dict()
    args['state'] = module.params['state']
    args['api_key'] = module.params['api_key']
    args['zone'] = module.params['zone']
    args['type'] = module.params['type']
    args['record'] = module.params['record']
    args['address'] = module.params['address']
    args['priority'] = module.params['priority']
    args['relative'] = module.params['relative']
    args['ttl'] = module.params['ttl']
    args['check_mode'] = module.check_mode

    # perform some Memset API-specific validation
    # https://www.memset.com/apidocs/methods_dns.html#dns.zone_record_create
    failed_validation = False

    # priority can only be integer 0 > 999
    if not 0 <= args['priority'] <= 999:
        failed_validation = True
        error = 'Priority must be in the range 0 > 999 (inclusive).'
    # data value must be max 250 chars
    if len(args['address']) > 250:
        failed_validation = True
        error = "Data must be less than 250 characters in length."
    # record value must be max 250 chars
    if args['record']:
        if len(args['record']) > 63:
            failed_validation = True
            error = "Record must be less than 63 characters in length."
    # relative isn't used for all record types
    if args['relative']:
        if args['type'] not in ['CNAME', 'MX', 'NS', 'SRV']:
            failed_validation = True
            error = "Relative is only valid for CNAME, MX, NS and SRV record types"
    # if any of the above failed then fail early
    if failed_validation:
        module.fail_json(failed=True, msg=error, stderr=error)

    retvals = create_or_delete(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
