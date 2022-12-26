#!/usr/bin/env python3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError, AnsibleParserError

import os
import yaml
import json


DOCUMENTATION = r"""
    name: edpm_plugin
    plugin_type: inventory
    short_description: Returns Ansible inventory from yaml file.
    description: Returns Ansible inventory from yaml file.
    options:
      plugin:
          description: Name of the plugin
          required: true
          choices: ['edpm_plugin']
      path_to_inventory:
        description: Directory location of the yaml edpm inventory
        required: true
      inventory_file:
        description: File name of the yaml inventory file
        required: true
"""

class InventoryModule(BaseInventoryPlugin):
    NAME = "edpm_plugin"

    def __init__(self):
        self.hosts = []
        self.vars = {}
        # super().__init__()
  
    def verify_file(self, path):
        valid = True
        if super(InventoryModule, self).verify_file(path):
            #base class verifies that file exists 
            #and is readable by current user
            if path.endswith(('inventory.yaml',
                              'inventory.yml', 'edpm_inventory.yaml', 'edpm_inventory.yml')):
                valid = True
        return valid

    def _get_structured_inventory(self, inventory_file):
    
        #Initialize a dict
        # inventory_data = {}
        # Load the environment variable Running into bug here
        # env_var = os.environ['RUNNER_INVENTORY']
        # # Parse the environment variable as YAML
        # data = yaml.safe_load(env_var)
        
        # Load the YAML file
        with open(inventory_file, 'r') as f:
            data = yaml.safe_load(f)
        return data

    def _populate(self):
        self.inventory_file = self.inv_dir + '/' + self.inv_file
        self.myinventory = self._get_structured_inventory(self.inventory_file)
        
        # Recursively traverse the data to find the Compute group
        def traverse(data):
            if 'Compute' in data:
                return data['Compute']
            for _, group_data in data.items():
                if 'children' in group_data:
                    compute_group = traverse(group_data['children'])
                    if compute_group:
                        return compute_group
            return None

        compute_group = traverse(self.myinventory)

        # Extract the hosts and variables from the Compute group
        if compute_group:
            if 'hosts' in compute_group:
                for host_name, host_data in compute_group['hosts'].items():
                    self.hosts.append(host_name)
                    self.vars[host_name] = host_data
            if 'vars' in compute_group:
                for host_name, host_vars in compute_group['vars'].items():
                    try:
                        self.vars[host_name].update(host_vars)
                    except KeyError:
                        self.vars[host_name] = host_vars       

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache=True)
        # Read the inventory YAML file
        self._read_config_data(path)
        try:
            # Store the options from the YAML file
            self.plugin = self.get_option('plugin')
            self.inv_dir = self.get_option('path_to_inventory')
            self.inv_file = self.get_option('inventory_file')
        except Exception as e:
            raise AnsibleParserError(
                'All correct options required: {}'.format(e))

        # Call our internal helper to populate the dynamic inventory
        self._populate()
        
        self.inventory.add_group('compute')
        for host_name, host_vars in self.vars.items():
            if host_name not in self.hosts:
                self.inventory.set_variable('compute', host_name, host_vars)
            else:
                self.inventory.add_host(host_name, group='compute')
                self.inventory.set_variable(host_name, 'vars', host_vars)

