"""Wrapper class for registry-related shell commands."""
import time
import argparse
from ice import ascii_table
from . import ShellExt


class RegistryShell(ShellExt):
    """Wrapper class for registry-related shell commands."""

    def __init__(self, registry, logger, debug=False):
        """
        :param ice.registry.client.RegistryClient registry:
        :param logging.Logger logger:
        :param bool debug: Set to True for debug behaviour.
        """
        self.registry = registry
        super(RegistryShell, self).__init__(logger, debug)

    def start(self, shell):
        """Starts the shell extension.

        It initializes the extension object and calls the
        shell.add_command to setup the shell hooks.

        :param ice_shell.Shell shell:
        """
        super(RegistryShell, self).start(shell)
        shell.add_command('inst_ls', self.ls_inst)
        shell.add_command(
            'inst_wait', self.run_wait,
            parser=self.get_wait_parser()
        )
        shell.add_command(
            'inst_del', self.del_inst,
            usage='<Instance id> [<Instance id> ...]'
        )
        shell.add_command(
            'inst_show', self.show_inst,
            usage='<Instance id> [<Instance id> ...]'
        )

    def ls_inst(self):
        """Lists instances."""
        inst_list = self.registry.get_instances_list(
            self.shell.get_session()
        )
        if inst_list is None:
            self.logger.error('Failed to find instances!')
            return

        self.logger.info('Found %d instances' % len(inst_list))
        table = ascii_table.ASCIITable()
        table.add_column('id', ascii_table.ASCIITableColumn('Id', 27))
        table.add_column('public_ip_addr',
                         ascii_table.ASCIITableColumn('Public IP', 23))
        table.add_column('cloud_id',
                         ascii_table.ASCIITableColumn('Cloud Id', 30))

        for inst in inst_list:
            table.add_row({
                'id': inst.id,
                'public_ip_addr': inst.public_ip_addr,
                'cloud_id': inst.cloud_id
            })

        print(ascii_table.ASCIITableRenderer().render(table))

    def get_wait_parser(self):
        parser = argparse.ArgumentParser(prog='inst_wait', add_help=False)
        parser.add_argument(
            '-n', metavar='<Amount of instances>', dest='amt', type=int,
            default=1
        )
        parser.add_argument(
            '-t', metavar='<Timeout (sec.)>', dest='timeout', default=120
        )
        return parser

    def run_wait(self, args):
        """Waits for instances to appear."""
        res = self._wait(args.amt, args.timeout)
        if res:
            self.logger.info('Instances are ready!')
        else:
            self.logger.error('Timeout!')

    def _wait(self, amt, timeout=120):
        """Wait for `amt` number of instances to appear in the pool.

        :param int amt: The expected number of instances.
        :param int timeout: The timeout of the command, in seconds.
        :param ice.entities.Session sess: The current session.
        :rtype: bool
        :return: `True` if the condition is satisfied and `False` on time out
            or error.
        """
        seconds = 0
        while seconds < timeout:
            instances = self.registry.get_instances_list(
                self.shell.get_session()
            )
            if len(instances) < amt:
                seconds += 5
                self.logger.debug(
                    '{0:d} instances found, sleeping for 5 seconds...'
                    .format(len(instances))
                )
                time.sleep(5)
                continue
            return True

        return False

    def show_inst(self, *inst_ids):
        """Shows information for a specific instance."""
        if len(inst_ids) == 0:
            self.logger.error('Please specify an instance id!')
            return

        for inst_id in inst_ids:
            print('-' * 80)
            print('Instance {:s}'.format(inst_id))
            print('-' * 80)

            inst = self.registry.get_instance(inst_id)
            if inst is None:
                self.logger.error('Failed to find instance `%s`!' % inst_id)
                continue

            # Compose info
            info = [
                ('Session Id', inst.session_id),
                ('Public IP address', inst.public_ip_addr),
                ('Public reverse DNS', inst.public_reverse_dns),
                ('SSH username', inst.ssh_username),
                ('SSH port', inst.ssh_port),
                ('SSH authorized fingerprint', inst.ssh_authorized_fingerprint)
            ]

            # Printout info
            for key, value in info:
                print('{}:'.format(key))
                print('  {}'.format(value))

            print('-' * 80)

    def del_inst(self, *inst_ids):
        """Deletes a specific instance."""
        if len(inst_ids) == 0:
            self.logger.error('Please specify an instance id!')
            return

        for inst_id in inst_ids:
            inst = self.registry.get_instance(inst_id)
            if inst is None:
                self.logger.error('Failed to find instance `%s`!' % inst_id)
                continue

            if not self.registry.delete_instance(inst):
                self.logger.error('Failed to delete instance `%s`!' % inst_id)
                continue
            else:
                self.logger.info(
                    'Instance `%s` was successfully deleted.' % inst_id
                )
