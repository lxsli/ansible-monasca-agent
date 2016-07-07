#!/usr/bin/python
# (C) Copyright 2015 Hewlett-Packard Development Company, L.P.

DOCUMENTATION = '''
---
module: monasca_agent_plugin
short_description: Configure the Monasca agent by running the given monasca-setup detection plugin.
description:
    This module uses the --detection_plugins option of monasca-setup and it is assumed that the full primary configuration of monasca-setup has already
    been done. This primary configuration is done when running the monasca-agent ansible role this module is found in.
    - Monasca project homepage - https://wiki.openstack.org/wiki/Monasca
author: Tim Kuhlman <tim@backgroundprocess.com>
requirements: [ ]
options:
    args:
        required: false
        description:
            - A string containing arguments passed to the detection plugin
    name:
        required: false
        description:
            - The name of the detection plugin to run, this or names is required.
    names:
        required: false
        description:
            - A list of detection plugins to run, this or name is required.
    state:
        required: false
        default: "configured"
        choices: [ configured, absent ]
        description:
            - If the state is configured the detection plugin will be run causing updates if needed. If absent the configuration created by the
              detection_plugins will be removed.
    monasca_setup_path:
        required: false
        default: "/opt/monasca/bin/monasca-setup"
        description:
            - The path to the monasca-setup command.
'''

EXAMPLES = '''
tasks:
    - name: Monasca agent ntp plugin configuration
      monasca_agent_plugin: name="ntp"
    - name: Monasca agent plugin configuration
      monasca_agent_plugin:
        names:
            - ntp
            - mysql
'''

import json

from ansible.module_utils.basic import *


def main():
    module = AnsibleModule(
        argument_spec=dict(
            args=dict(required=False, type='str'),
            data=dict(required=False, type='raw'),
            name=dict(required=False, type='str'),
            names=dict(required=False, type='list'),
            state=dict(default='configured', choices=['configured', 'absent'], type='str'),
            monasca_setup_path=dict(default='/opt/monasca/bin/monasca-setup', type='str'),

            # ServicePlugin arguments, accepted for convenience.
            # Unfortunately argument_spec doesn't support varargs so other plugins
            # with deeply structured config will need to use 'data'.
            service_name=dict(required=False, type='str'),
            process_names=dict(required=False, type='list'),
            file_dirs_names=dict(required=False, type='raw'),
            directory_names=dict(required=False, type='list'),
            service_api_url=dict(required=False, type='str'),
            match_pattern=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    if module.params['names'] is None and module.params['name'] is None:
        module.fail_json(msg='Either name or names paramater must be specified')

    if module.params['names'] is not None:
        names = module.params['names']
    else:
        names = [module.params['name']]

    args = [module.params['monasca_setup_path']]
    if module.check_mode:
        args.append('--dry_run')
    if module.params['state'] == 'absent':
        args.append('-r')
    args.append('--detection_plugins')
    args.extend(names)

    data = {k: v for k, v in module.params.items()
            if k in ['service_name', 'process_names', 'file_dirs_names',
                     'directory_names', 'service_api_url', 'match_pattern']}
    if module.params['data'] is not None:
        args.extend(['--detection_args_json', json.dumps(module.params['data'])])
    elif any(v for k, v in data.items()):
        args.extend(['--detection_args_json', json.dumps(data)])
    elif module.params['args'] is not None:
        args.extend(['--detection_args', module.params['args']])

    rc, out, err = module.run_command(args, check_rc=True)
    if err.find('Not all plugins found') != -1:
        module.fail_json(msg='Some specified plugins were not found.', stdout=out.rstrip("\r\n"), stderr=err.rstrip("\r\n"))

    if err.find('No changes found') == -1:
        changed = True
    else:
        changed = False

    module.exit_json(changed=changed, cmd=args, stdout=out.rstrip("\r\n"), stderr=err.rstrip("\r\n"), rc=rc)

if __name__ == "__main__":
    main()
