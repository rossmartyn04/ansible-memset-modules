#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
from time import sleep
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
short_description: Request reload of Memset's DNS infrastructure
notes:
  - DNS reload requests are a best-effort service provided by Memset; these generally
    happen every 15 minutes by default, however you can request an immediate reload if
    later tasks rely on the records being created. An API key generated via the
    Memset customer control panel is required with the following minimum scope:
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
            - Boolean value, if set will poll the reload job status
'''

EXAMPLES = '''
- name: request DNS reload
  local_action: memset_dns_reload:
    api_key=5eb86c9196ab03919abcf03857163741
    poll=true
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


#def reload_dns(args):


def main():
    has_changed, has_failed = False, False
    memset_api, msg = None, None
    retvals = dict()

    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, type='str', no_log=True),
            poll=dict(required=False, default=False, type='bool')
        ),
    )

    api_key = module.params['api_key']
    poll = module.params['poll']

    payload = dict()
    api_method = 'dns.reload'

    has_failed, msg, response = memset_api_call(api_key=api_key, api_method=api_method, payload=payload)

    if not has_failed:
        has_changed = True
        memset_api = response.json()

    if poll:
        payload['id'] = response.json()['id']
        api_method = 'job.status'

        _, _, response = memset_api_call(api_key=api_key, api_method=api_method, payload=payload)

        while not response.json()['finished']:
            counter = 0
            while counter < 6:
                sleep(5)
                _, msg, response = memset_api_call(api_key=api_key, api_method=api_method, payload=payload)
                counter += 1
        if response.json()['error']:
            module.fail_json(failed=True, msg=msg, stderr='Memset API returned job error', memset_api=response.json())
        else:
            memset_api = response.json()

    # assemble return variables
    retvals['failed'] = has_failed
    retvals['changed'] = has_changed
    if msg is not None:
        retvals['msg'] = msg
    if memset_api is not None:
        retvals['memset_api'] = msg

    if has_failed:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
