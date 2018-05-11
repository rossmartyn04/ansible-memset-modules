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
module: memset_dns_reload
author: "Simon Weald (@analbeard)"
version_added: "2.6"
short_description: Request reload of Memset's DNS infrastructure
notes:
  - DNS reload requests are a best-effort service provided by Memset; these generally
    happen every 15 minutes by default, however you can request an immediate reload if
    later tasks rely on the records being created. An API key generated via the
    Memset customer control panel is required with the following minimum scope -
    `dns.reload`. If you wish to poll the job status to wait until the reload has
    completed, then `job.status` is also required.
description:
    - Request a reload of Memset's DNS infrastructure, and optionally poll until it finishes.
options:
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel
    poll:
        default: false
        type: bool
        description:
            - Boolean value, if set will poll the reload job's status and return
              when the job has completed (unless the 30 second timeout is reached first).
              If the timeout is reached then the task will not be marked as failed, but
              stderr will indicate that the polling failed.
requirements:
    - "requests"
'''

EXAMPLES = '''
- name: submit DNS reload and poll
  memset_dns_reload:
    api_key: 5eb86c9196ab03919abcf03857163741
    poll: True
  delegate_to: localhost
'''

RETURN = '''
---
memset_api:
  description: Raw response from the Memset API
  returned: always
  type: complex
  contains:
    error:
      description: Whether the job ended in error state
      returned: always
      type: bool
      sample: true
    finished:
      description: Whether the job completed before the result was returned
      returned: always
      type: bool
      sample: true
    id:
      description: Job ID
      returned: always
      type: string
      sample: "c9cc8ad2a3e3fb8c63ed83c424928ef8"
    status:
      description: Job status
      returned: always
      type: string
      sample: "DONE"
    type:
      description: Job type
      returned: always
      type: string
      sample: "dns"
'''

from time import sleep
from ansible.module_utils.memset import memset_api_call

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def poll_reload_status(api_key=None, job_id=None, payload=None):
    memset_api, stderr, msg = None, None, None
    payload['id'] = job_id

    api_method = 'job.status'
    _has_failed, _msg, response = memset_api_call(api_key=api_key, api_method=api_method, payload=payload)

    while not response.json()['finished']:
        counter = 0
        while counter < 6:
            sleep(5)
            _has_failed, msg, response = memset_api_call(api_key=api_key, api_method=api_method, payload=payload)
            counter += 1
    if response.json()['error']:
        # the reload job was submitted but polling failed. Don't return this as an overall task failure.
        stderr = "Reload submitted successfully, but the Memset API returned a job error when attempting to poll the reload status."
        msg = msg
    else:
        memset_api = response.json()
        msg = None

    return(memset_api, msg, stderr)


def reload_dns(args=None):
    retvals, payload = dict(), dict()
    has_changed, has_failed = False, False
    memset_api, msg, stderr = None, None, None

    api_method = 'dns.reload'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    if has_failed:
        retvals['failed'] = has_failed
        retvals['memset_api'] = response.json()
        retvals['msg'] = msg
        return(retvals)

    # set changed to true if the reload request was accepted
    has_changed = True
    memset_api = msg
    # empty msg var as we don't want to return the API's json response twice
    msg = None

    if args['poll']:
        job_id = response.json()['id']
        memset_api, msg, stderr = poll_reload_status(api_key=args['api_key'], job_id=job_id, payload=payload)

    # assemble return variables
    retvals['failed'] = has_failed
    retvals['changed'] = has_changed
    for val in ['msg', 'stderr', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, type='str', no_log=True),
            poll=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=False
    )

    if not HAS_REQUESTS:
        module.fail_json(msg='requests required for this module')

    args = dict()
    for key, arg in module.params.items():
        args[key] = arg

    retvals = reload_dns(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
