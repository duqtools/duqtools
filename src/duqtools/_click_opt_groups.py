"""Module with click subclasses to group options in `--help`output.

Example:

    python _click_opt_groups.py --help

Implementation based on:
https://github.com/pallets/click/issues/373#issuecomment-515293746
"""
from __future__ import annotations

from collections import defaultdict

import click


class GroupOpt(click.Option):

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)


class GroupCmd(click.Command):

    def format_options(self, ctx, formatter):
        """Writes all the options into the formatter if they exist.

        Implementation based on:
        https://github.com/pallets/click/issues/373#issuecomment-515293746
        """
        sections = defaultdict(list)

        for param in self.get_params(ctx):
            option = param.get_help_record(ctx)
            if option:
                try:
                    title = str(param.group)
                except AttributeError:
                    title = 'Options'

                sections[title].append(option)

        for title, options in sections.items():
            with formatter.section(title):
                formatter.write_dl(options)


if __name__ == '__main__':

    @click.group()
    def cli():
        pass

    @cli.command(cls=GroupCmd)
    @click.option('-a')
    @click.option('-b', cls=GroupOpt, group='Group 1')
    @click.option('-c', cls=GroupOpt, group='Group 1')
    @click.option('-d', cls=GroupOpt, group='Group 2')
    @click.option('-e', cls=GroupOpt, group='Group 2')
    def main(**kwargs):
        print(kwargs)

    main()
