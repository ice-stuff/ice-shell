"""Wrapper class for Fabric-related shell commands."""
import os
from ice import experiment
from . import ShellExt

RUN_EXP_USAGE = '<Experiment name> [<Tag key>=<Tag value>]' + \
    ' <Task or runner name> [<Arguments> ...]'


class ExperimentShell(ShellExt):
    """Wrapper class for Fabric-related shell commands."""

    def __init__(self, registry, ssh_cfg, logger, debug=False):
        """
        :param ice.registry.client.RegistryClient registry:
        :param ice.experiment.CfgSSH ssh_cfg:
        :param logging.Logger logger:
        :param bool debug: Set to True for debug behaviour.
        """
        self.registry = registry
        self.ssh_cfg = ssh_cfg
        self._experiments = {}
        super(ExperimentShell, self).__init__(logger, debug)

    def start(self, shell):
        """Starts the shell extension.

        It initializes the extension object and calls the
        shell.add_command to setup the shell hooks.

        :param ice_shell.Shell shell:
        """
        super(ExperimentShell, self).start(shell)

        shell.add_command(
            'exp_load', self.load_exp, usage='<Experiment file path>'
        )
        shell.add_command(
            'exp_ls', self.ls_exp, usage='<Experiment name>'
        )
        shell.add_command('exp_run', self.run_exp, usage=RUN_EXP_USAGE)

    def load_exp(self, *args):
        """Loads an experiment to iCE."""
        args = list(args)

        try:
            path = args.pop(0)
        except IndexError:
            self.logger.error('Please specify experiment path!')
            return

        experiment_name = os.path.basename(path).replace(
            '.py', ''
        )
        if experiment_name in self._experiments:
            exp = self._experiments.get(experiment_name)
            try:
                exp.load()
            except experiment.Experiment.LoadError as err:
                self.logger.error(
                    'Module `{0:s}` failed to be re-loaded: {1:s}'
                    .format(experiment_name, str(err))
                )
            return
        else:
            try:
                exp = experiment.Experiment(self.logger, path)
            except experiment.Experiment.LoadError as err:
                self.logger.error(
                    'Loading module `%s`: %s' % (path, err)
                )
                return
            self._experiments[experiment_name] = exp
        self.logger.info('Module `%s` is successfully loaded!' % path)

    def ls_exp(self, *args):
        args = list(args)

        try:
            experiment_name = args.pop(0)
            if experiment_name not in self._experiments:
                self.logger.error(
                    'Experiment `%s` is not loaded!' % experiment_name
                )
                return
            exp = self._experiments[experiment_name]
        except IndexError:
            self.logger.error('Please specify experiment name!')
            return

        tasks, runners = exp.get_contents()
        print('> Module `%s`:' % experiment_name)
        if len(runners) > 0:
            print('Runners:')
            print('\n'.join(runners))
        if len(tasks) > 0:
            print('Tasks:')
            print('\n'.join(tasks))

    def _parse_run_exp_args(self, args):
        # empty?
        if len(args) == 0:
            return None

        parsed_args = {
            'experiment_name': args.pop(0),
            'tag_key': None,
            'tag_value': None,
            'func_name': 'run',
            'args': []
        }

        # that's it?
        if len(args) == 0:
            return parsed_args
        # has tag?
        if '=' in args[0]:
            tag_pair = args.pop(0)
            tag_parts = tag_pair.split('=', 1)
            if len(tag_parts) != 2:
                return parsed_args
            parsed_args['tag_key'] = tag_parts[0]
            parsed_args['tag_value'] = tag_parts[1]
        # that's it?
        if len(args) == 0:
            return parsed_args
        # the rest
        parsed_args['func_name'] = args.pop(0)
        parsed_args['args'] = args

        return parsed_args

    def _find_experiment(self, experiment_name):
        if experiment_name not in self._experiments:
            return None
        return self._experiments[experiment_name]

    def _filter_instances(self, instances, tag_key, tag_value):
        if tag_key is None:
            return instances

        ret_val = []
        for inst in instances:
            if tag_key not in inst.tags:
                continue  # can't find tag by this key
            if tag_value is not None and inst.tags[tag_key] != tag_value:
                continue  # tag value is not the required one
            ret_val.append(inst)

        return ret_val

    def run_exp(self, *args):
        """Runs a task or an experiment."""
        parsed_args = self._parse_run_exp_args(list(args))
        if parsed_args is None:
            self.logger.error('USAGE: exp_run {:s}'.format(RUN_EXP_USAGE))
            return

        exp = self._find_experiment(parsed_args['experiment_name'])
        if exp is None:
            self.logger.error('Experiment `{:s}` is not loaded!'.format(
                parsed_args['experiment_name']
            ))
            return

        instances = self.registry.get_instances_list(self.shell.get_session())
        filtered_instances = self._filter_instances(
            instances, parsed_args['tag_key'], parsed_args['tag_value']
        )
        if len(filtered_instances) == 0:
            self.logger.info('No instances to run against')
            return

        res = exp.run(
            filtered_instances, self.ssh_cfg,
            parsed_args['func_name'], args=parsed_args['args']
        )
        if res is False:
            self.logger.error('Task `{:s}.{:s}` failed!'.format(
                parsed_args['experiment_name'], parsed_args['func_name']
            ))
