from ansible import context
from ansible.cli import CLI
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
import os

loader = DataLoader()

context.CLIARGS = ImmutableDict(tags={}, listtags=False, listtasks=False,
                                listhosts=False, syntax=False,
                                connection='ssh',
                                module_path=None, forks=100, remote_user='xxx',
                                private_key_file=None,
                                ssh_common_args=None, ssh_extra_args=None,
                                sftp_extra_args=None, scp_extra_args=None,
                                become=True, become_method='sudo',
                                become_user='root', verbosity=True,
                                check=False, start_at_task=None)


class ansible_runner:

    def __init__(self, inv_location, pb_location, pb_name=None):

        self.inventory_location = inv_location
        self.playbook_location = pb_location
        self.playbook_name = pb_name

        self.inventory = InventoryManager(
                loader=loader, sources=(self.inventory_location,)
        )

        self.variable_manager = VariableManager(
            loader=loader, inventory=self.inventory,
            version_info=CLI.version_info(gitinfo=False)
        )

        self.pbex = PlaybookExecutor(
            playbooks=['{0}/{1}'.format(
                self.playbook_location, self.playbook_name
            )],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=loader, passwords={}
        )

    def playbook_runner(self):

        return self.pbex.run()


if __name__ == '__main__':

    path_to_ansible = '/Users/kapilmathur/My_ansible_journey/ping_with_ansible'
    path_to_inventory = os.path.join(path_to_ansible, 'inventory.txt')
    path_to_playbook = path_to_ansible
    playbook_name = 'default_ssh_port.yaml'

    pb_runner = ansible_runner(
        inv_location=path_to_inventory, pb_location=path_to_ansible,
        pb_name=playbook_name
    )

    results = pb_runner.playbook_runner()
