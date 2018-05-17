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
module: memset_api_key
author: "Simon Weald (@analbeard)"
version_added: "2.6"
short_description: Create, delete and amend API keys for use with the Memset API.
notes:
  - API keys can be used to perform a variety of tasks via the Memset API. Their
    scope can be limited on creation so that it is possible to create API keys
    with just a single purpose. Generating a key with this module requires an
    existing key with the following scopes - I(apikey.add_scope), I(apikey.create),
    I(apikey.delete), I(apikey.delete_scope), I(apikey.info), I(apikey.list).
description:
    - Create, delete and amend API keys for use with the Memset API.
options:
    state:
        required: true
        description:
            - Indicates desired state of resource.
        choices: [ absent, present ]
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel.
    comment:
        required: true
        description:
            - A comment by which to identify the key.
    methods:
        required: false
        type: list
        description:
            - List of API methods which the generated key is authorised for. See
              U(https://www.memset.com/apidocs/methods_apikey.html#scopes)
    servers:
        required: false
        type: list
        description:
            - List of servers which the generated key is allowed to act against.
              See U(https://www.memset.com/apidocs/methods_apikey.html#scopes).
'''

EXAMPLES = '''
- name: create an unrestricted API key
  memset_api_key:
    comment: "Unrestricted key"
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
  delegate_to: localhost

- name: create an API key for creating DNS records only
  memset_api_key:
    comment: "DNS record management key"
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
    methods:
      - "dns.zone_record_create"
      - "dns.zone_record_delete"
      - "dns.zone_record_info"
      - "dns.zone_record_list"
      - "dns.zone_record_update"

- name: create a key which can reboot a single server
  memset_api_key:
    comment: "key for rebooting testyaa1"
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
    methods:
      - "server.reboot"
    servers:
      - "testyaa1"
'''

RETURN = '''
---
memset_api:
  description: Info from the Memset API
  returned: when changed or state == present
  type: complex
  contains:
    comment:
      description: Comment describing the key.
      returned: always
      type: string
      sample: "my test key"
    created:
      description: Date stamp of key creation.
      returned: always
      type: string
      sample: "2018-05-17 22:04:47"
    key:
      description: The generated API key.
      returned: always
      type: string
      sample: "794e8ccfdd484692a2ad649a2a8ba1a5"
    scopes:
      description: A list of scopes applied to the key.
      returned: always
      type: dict
      sample: '{
        "method": [
          "dns.reload"
        ],
        "name": [
          "testyaa1"
        ]
      }'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import memset_api_call


def api_validation(args=None):
    '''
    Perform some validation which will be enforced by Memset's API (see:
    https://www.memset.com/apidocs/methods_apikey.html#apikey.create).
    '''
    # comment length must be less than 250 chars
    if len(args['comment']) > 255:
        stderr = 'Comment must be less than 255 characters in length.'
        module.fail_json(failed=True, msg=stderr, stderr=stderr)


def create_key(args=None, payload=None):
    api_method = 'apikey.create'


def delete_key(args=None, payload=None):
    api_method = 'apikey.delete'


def add_scopes(args=None, payload=None):
    api_method = 'apikey.add_scope'


def remove_scopes(args=None, payload=None):
    api_method = 'apikey.delete_scope'


def create_or_delete_key(args=None):
    api_method = 'apikey.info'
    api_method = 'apikey.list'


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            comment=dict(required=True, type='str'),
            methods=dict(required=False, type='list'),
            servers=dict(required=False, type='list')
        ),
        supports_check_mode=True
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg
    args['check_mode'] = module.check_mode

    retvals = create_or_delete_key(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
