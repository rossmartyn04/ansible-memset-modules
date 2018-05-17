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
module: memset_MODULE
author: "Simon Weald (@analbeard)"
version_added: "2.6"
short_description: Do something with something at Memset.
notes:
  - Zone domains can be thought of as a collection of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the
    Memset customer control panel is needed with the following minimum scope -
    I(dns.zone_domain_create), I(dns.zone_domain_delete), I(dns.zone_domain_list).
description:
    - Do something with something at Memset.
options:
    state:
        required: true
        description:
            - Indicates desired state of resource.
        choices: [ absent, present ]
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
---
memset_api:
  description: Info from the Memset API
  returned: when changed or state == present
  type: complex
  contains:
    resource:
      description: short description
      returned: always
      type: string
      sample: "asdfasdfasdf"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import memset_api_call


def api_validation(args=None):


def create_stuff(args=None, payload=None):


def delete_stuff(args=None, payload=None):


def create_or_delete_stuff(args=None):


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, type='str', no_log=True)
        ),
        supports_check_mode=False
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg

    retvals = create_or_delete_stuff(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
