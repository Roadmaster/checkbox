# This file is part of Checkbox.
#
# Copyright 2012, 2013, 2014 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`plainbox.provider_manager` -- CLI tools for managing providers
====================================================================

This module has strict API stability requirements. The only public API is the
:func:`setup()` function and the argument handling semantics that is documented
therein.
"""

import argparse
import inspect
import logging
import os
import re
import shutil
import subprocess
import tarfile

from plainbox import __version__ as version
from plainbox.i18n import docstring
from plainbox.i18n import gettext as _
from plainbox.i18n import gettext_noop as N_
from plainbox.impl.commands import ToolBase, CommandBase
from plainbox.impl.job import JobDefinition
from plainbox.impl.job import Problem
from plainbox.impl.job import ValidationError as JobValidationError
from plainbox.impl.logging import setup_logging
from plainbox.impl.providers.v1 import get_user_PROVIDERPATH_entry
from plainbox.impl.secure.config import Unset
from plainbox.impl.secure.config import ValidationError \
    as ConfigValidationError
from plainbox.impl.secure.providers.v1 import Provider1
from plainbox.impl.secure.providers.v1 import Provider1Definition
from plainbox.impl.secure.rfc822 import RFC822SyntaxError

__all__ = ['setup']


_logger = logging.getLogger("plainbox.provider_manager")


class ManageCommand(CommandBase):
    """
    Base class for all management commands.

    This class encapsulates the provider definition that its subclasses are
    going to work with. Using the :meth:`get_provider()` method you can load
    the provider that is being worked on even if it's not in PROVIDERPATH.
    """

    gettext_domain = "plainbox"

    def __init__(self, definition):
        """
        Initialize a new ManageCommand instance with the specified provider.

        :param provider:
            A Provider1Definition that describes the provider to encapsulate
        """
        self._definition = definition

    @property
    def definition(self):
        """
        a Provider1Definition object that describes the current provider
        """
        return self._definition

    def get_provider(self):
        """
        Get a Provider1 that describes the current provider
        """
        return Provider1.from_definition(self.definition, secure=False)


@docstring(
    # TRANSLATORS: please leave various options (both long and short forms),
    # environment variables and paths in their original form. Also keep the
    # special @EPILOG@, @UNIX_LAYOUT@ and @FLAT_LAYOUT@ strings. The first line
    # of the translation is special and is used as the help message. Please
    # keep the pseudo-statement form and don't finish the sentence with a dot.
    # Pay extra attention to whitespace.  It must be correctly preserved or the
    # result won't work. In particular the leading whitespace *must* be
    # preserved and *must* have the same length on each line.
    N_("""
    install this provider in the system

    This command installs the provider to the specified prefix.

    @EPILOG@

    Installation Layouts
    ====================

    There are two possible installation layouts: flat, perfect for keeping the
    whole provider in one directory, and unix, which is optimized for
    packaging and respecting the filesystem hierarchy.

    In both cases, a generated file is created at a fixed location:

        {prefix}/share/plainbox-providers-1/{provider.name}.provider

    This file is essential for plainbox to discover providers. It contains
    meta-data collected from the manage.py setup() call.

    For Packaging
    -------------

    System-wide installations should typically use `--prefix=/usr` coupled
    with `--layout=unix`. For packaging you will want to use the `--root=`
    argument to place all of the copied and generated files into your packaging
    system staging area. This will not affect generated content, which only
    respects the prefix argument.

    UNIX Layout
    -----------

    In the unix layout, following transformation is applied:

    @LAYOUT[unix]@

    Flat Layout
    -----------

    @LAYOUT[flat]@
    """))
class InstallCommand(ManageCommand):

    # Template of the .provider file
    _PROVIDER_TEMPLATE = os.path.join(
        '{prefix}', 'share', 'plainbox-providers-1',
        '{provider.name_without_colon}.provider')

    # Template of the location= entry
    _LOCATION_TEMPLATE = os.path.join(
        '{prefix}', 'lib', 'plainbox-providers-1',
        '{provider.name_without_colon}')

    # Templates for various installation layouts
    _INSTALL_LAYOUT = {
        'unix': {
            'bin': os.path.join(
                '{prefix}', 'lib', '{provider.name}', 'bin'),
            'build/mo': os.path.join('{prefix}', 'share', 'locale'),
            'data': os.path.join(
                '{prefix}', 'share', '{provider.name}', 'data'),
            'jobs': os.path.join(
                '{prefix}', 'share', '{provider.name}', 'jobs'),
            'po': None,
            'whitelists': os.path.join(
                '{prefix}', 'share', '{provider.name}', 'whitelists'),
        },
        'flat': {
            'bin': os.path.join(
                '{prefix}', 'lib', 'plainbox-providers-1', '{provider.name}',
                'bin'),
            'build/mo': os.path.join(
                '{prefix}', 'lib', 'plainbox-providers-1', '{provider.name}',
                'locale'),
            'data': os.path.join(
                '{prefix}', 'lib', 'plainbox-providers-1', '{provider.name}',
                'data'),
            'jobs': os.path.join(
                '{prefix}', 'lib', 'plainbox-providers-1', '{provider.name}',
                'jobs'),
            'po': None,
            'whitelists': os.path.join(
                '{prefix}', 'lib', 'plainbox-providers-1', '{provider.name}',
                'whitelists'),
        }
    }

    # Mapping from directory name to .provider entry name
    _DEF_MAP = {
        'bin': 'bin_dir',
        'build/mo': 'locale_dir',
        'data': 'data_dir',
        'jobs': 'jobs_dir',
        'whitelists': 'whitelists_dir'
    }

    def get_command_epilog(self):
        def format_layout(layout):
            return '\n'.join(
                # TRANSLATORS: not installed as in 'will not be installed'
                '    * {:10} => {}'.format(src, _("not installed"))
                if dest is None else
                '    * {:10} => {}'.format(src, dest)
                for src, dest in sorted(layout.items())
            )
        return re.sub(
            '@LAYOUT\[(\w+)]@',
            lambda m: format_layout(self._INSTALL_LAYOUT[m.group(1)]),
            super().get_command_epilog())

    def register_parser(self, subparsers):
        """
        Overridden method of CommandBase.

        :param subparsers:
            The argparse subparsers objects in which command line argument
            specification should be created.

        This method is invoked by the command line handling code to register
        arguments specific to this sub-command. It must also register itself as
        the command class with the ``command`` default.
        """
        parser = self.add_subcommand(subparsers)
        parser.add_argument(
            "--prefix", default="/usr/local", help=_("installation prefix"))
        parser.add_argument(
            '--layout',
            default='flat',
            choices=sorted(self._INSTALL_LAYOUT.keys()),
            # TRANSLATORS: don't translate %(defaults)s
            help=_("installation directory layout (default: %(default)s)"))
        parser.add_argument(
            "--root", default="",
            help=_("install everything relative to this alternate root"
                   " directory"))
        parser.set_defaults(command=self)

    def invoked(self, ns):
        """
        Overridden method of CommandBase.

        :param ns:
            The argparse namespace object with parsed argument data

        :returns:
            the exit code of ./manage.py install

        This method is invoked when all of the command line arguments
        associated with this commands have been parsed and are ready for
        execution.
        """
        self._write_provider_file(ns.root, ns.prefix, ns.layout)
        self._copy_all_data(ns.root, ns.prefix, ns.layout)

    def _write_provider_file(self, root, prefix, layout):
        self._write_to_file(
            root, self._PROVIDER_TEMPLATE.format(
                prefix=prefix, provider=self.definition),
            lambda stream: self._get_provider_config_obj(
                layout, prefix).write(stream))

    def _copy_all_data(self, root, prefix, layout):
        dest_map = self._get_dest_map(layout, prefix)
        assert os.path.isabs(self.definition.location)
        for src_name, dst_name in dest_map.items():
            assert not os.path.isabs(src_name)
            assert os.path.isabs(dst_name)
            src_name = os.path.join(self.definition.location, src_name)
            dst_name = root + dst_name
            if os.path.exists(src_name):
                try:
                    os.makedirs(os.path.dirname(dst_name), exist_ok=True)
                except IOError:
                    pass
                _logger.info(_("copying: %s => %s"), src_name, dst_name)
                shutil.copytree(src_name, dst_name)
            else:
                _logger.warning(_("cannot copy %s, no such file or directory"),
                                src_name)

    def _get_dest_map(self, layout, prefix):
        # Compute directory layout
        dir_layout = self._INSTALL_LAYOUT[layout]
        return {
            src_name: dest_name_template.format(
                prefix=prefix, provider=self.definition)
            for src_name, dest_name_template in dir_layout.items()
            if dest_name_template is not None
        }

    def _get_provider_config_obj(self, layout, prefix):
        dest_map = self._get_dest_map(layout, prefix)
        # Create the .provider file config object
        config_obj = self.definition.get_parser_obj()
        section = 'PlainBox Provider'
        if layout == 'flat':
            # Treat the flay layout specially, just as it used to behave before
            # additional layouts were added. In this mode only the location
            # field is defined.
            config_obj.set(
                section, 'location', self._LOCATION_TEMPLATE.format(
                    prefix=prefix, provider=self.definition))
        else:
            # In non-flat layouts don't store location as everything is
            # explicit
            config_obj.remove_option(section, 'location')
            for src_name, key_id in self._DEF_MAP.items():
                if os.path.exists(os.path.join(self.definition.location,
                                               src_name)):
                    config_obj.set(section, key_id, dest_map[src_name])
        return config_obj

    def _write_to_file(self, root, pathname, callback):
        try:
            os.makedirs(root + os.path.dirname(pathname), exist_ok=True)
        except IOError:
            pass
        with open(root + pathname, 'wt', encoding='UTF-8') as stream:
            callback(stream)


@docstring(
    # TRANSLATORS: please leave various options (both long and short forms),
    # environment variables and paths in their original form. Also keep the
    # special @EPILOG@ string. The first line of the translation is special and
    # is used as the help message. Please keep the pseudo-statement form and
    # don't finish the sentence with a dot. Pay extra attention to whitespace.
    # It must be correctly preserved or the result won't work. In particular
    # the leading whitespace *must* be preserved and *must* have the same
    # length on each line.
    N_("""
    create a source tarball

    This commands creates a source distribution (tarball) of all of the
    essential provider files. This command takes no arguments and places the
    resulting tarball in the dist/ directory, relative to the ``manage.py``
    file. The tarball name is derived from provider name and version.

    @EPILOG@

    The items included in the tarball are:

    - the manage.py script itself
    - the README.md file
    - the jobs directory, and everything in it
    - the whitelists directory, and everything in it
    - the bin directory, and everything in it
    - the data directory, and everything in it
    - the po directory, and everything in it

    Any of the missing items are silently ignored.
    """))
class SourceDistributionCommand(ManageCommand):

    name = "sdist"

    _INCLUDED_ITEMS = ['manage.py', 'README.md', 'jobs', 'whitelists', 'bin',
                       'data', 'po']

    def register_parser(self, subparsers):
        """
        Overridden method of CommandBase.

        :param subparsers:
            The argparse subparsers objects in which command line argument
            specification should be created.

        This method is invoked by the command line handling code to register
        arguments specific to this sub-command. It must also register itself as
        the command class with the ``command`` default.
        """
        self.add_subcommand(subparsers)

    @property
    def dist_dir(self):
        return os.path.join(self.definition.location, "dist")

    @property
    def toplevel_name(self):
        return "{}-{}".format(
            self.definition.name.replace(":", "."),
            self.definition.version)

    @property
    def tarball_name(self):
        return os.path.join(
            self.dist_dir, "{}.tar.gz".format(self.toplevel_name))

    def invoked(self, ns):
        """
        Overridden method of CommandBase.

        :param ns:
            The argparse namespace object with parsed argument data

        :returns:
            the exit code of ./manage.py sdist

        This method is invoked when all of the command line arguments
        associated with this commands have been parsed and are ready for
        execution.
        """
        if not os.path.isdir(self.dist_dir):
            os.mkdir(self.dist_dir)
        with tarfile.open(self.tarball_name, mode="w:gz") as tarball:
            for name in self._INCLUDED_ITEMS:
                src_name = os.path.join(self.definition.location, name)
                dst_name = os.path.join(self.toplevel_name, name)
                if os.path.exists(src_name):
                    tarball.add(src_name, dst_name)


@docstring(
    # TRANSLATORS: please leave various options (both long and short forms),
    # environment variables and paths in their original form. Also keep the
    # special @EPILOG@ string. The first line of the translation is special and
    # is used as the help message. Please keep the pseudo-statement form and
    # don't finish the sentence with a dot. Pay extra attention to whitespace.
    # It must be correctly preserved or the result won't work. In particular
    # the leading whitespace *must* be preserved and *must* have the same
    # length on each line.
    N_("""
    install/remove this provider, only for development

    This commands creates or removes the ``.provider`` file describing the
    provider associated with this ``manage.py`` script. Unlike ``manage.py
    install`` the provider is installed without copying anything to a
    system-wide location and does not need to be re-executed after every
    change.

    The generated file removed by passing the ``--uninstall| -u`` option.

    @EPILOG@

    By default the .provider file is created in
    ``$XDG_DATA_HOME/plainbox-providers-1/`` directory. The filename is derived
    from the name of the provider (version is not included in the filename).

    Note that the full path of the source directory is placed in the generated
    file so you will need to re-run develop if you move this directory around.
    """))
class DevelopCommand(ManageCommand):

    def register_parser(self, subparsers):
        """
        Overridden method of CommandBase.

        :param subparsers:
            The argparse subparsers objects in which command line argument
            specification should be created.

        This method is invoked by the command line handling code to register
        arguments specific to this sub-command. It must also register itself as
        the command class with the ``command`` default.
        """
        parser = self.add_subcommand(subparsers)
        parser.add_argument(
            "-u", "--uninstall", default=False, action="store_true",
            # TRANSLATORS: don't translate the extension name
            help=_("remove the generated .provider file"))
        parser.add_argument(
            "-f", "--force", default=False, action="store_true",
            help=_("overwrite existing provider files"))

    def invoked(self, ns):
        pathname = os.path.join(
            get_user_PROVIDERPATH_entry(), "{}.provider".format(
                self.definition.name.replace(':', '.')))
        if ns.uninstall:
            if os.path.isfile(pathname):
                _logger.info(_("Removing provider file: %s"), pathname)
                os.unlink(pathname)
        else:
            if os.path.isfile(pathname) and not ns.force:
                print(_("Provider file already exists: {}").format(pathname))
                return 1
            else:
                _logger.info(_("Creating provider file: %s"), pathname)
                os.makedirs(os.path.dirname(pathname), exist_ok=True)
                with open(pathname, 'wt', encoding='UTF-8') as stream:
                    self.definition.write(stream)


@docstring(
    # TRANSLATORS: please leave various options (both long and short forms),
    # environment variables and paths in their original form. Also keep the
    # special @EPILOG@ string. The first line of the translation is special and
    # is used as the help message. Please keep the pseudo-statement form and
    # don't finish the sentence with a dot. Pay extra attention to whitespace.
    # It must be correctly preserved or the result won't work. In particular
    # the leading whitespace *must* be preserved and *must* have the same
    # length on each line.
    N_("""
    display basic information about this provider

    This command displays various essential facts about the provider associated
    with the ``manage.py`` script. Displayed data includes provider name and
    other meta-data, all of the jobs and whitelist, with their precise
    locations.
    """))
class InfoCommand(ManageCommand):

    def register_parser(self, subparsers):
        """
        Overridden method of CommandBase.

        :param subparsers:
            The argparse subparsers objects in which command line argument
            specification should be created.

        This method is invoked by the command line handling code to register
        arguments specific to this sub-command. It must also register itself as
        the command class with the ``command`` default.
        """
        self.add_subcommand(subparsers)

    def invoked(self, ns):
        provider = self.get_provider()
        print(_("[Provider MetaData]"))
        # TRANSLATORS: {} is the name of the test provider
        print("\t" + _("name: {}").format(provider.name))
        # TRANSLATORS: {} is the namenamespace of the test provider
        print("\t" + _("namespace: {} (derived from name)").format(
            provider.namespace))
        # TRANSLATORS: {} is the name of the test provider
        print("\t" + _("description: {}").format(provider.tr_description()))
        # TRANSLATORS: {} is the version of the test provider
        print("\t" + _("version: {}").format(provider.version))
        # TRANSLATORS: {} is the gettext translation domain of the provider
        print("\t" + _("gettext domain: {}").format(provider.gettext_domain))
        print(_("[Job Definitions]"))
        job_list, problem_list = provider.load_all_jobs()
        for job in job_list:
            # TRANSLATORS: the fields are as follows:
            # 0: job id
            # 1: pathname of the file the job is defined in
            print("\t" + _("{0!a}, from {1}").format(
                job.partial_id,
                job.origin.relative_to(self.definition.location)))
        if problem_list:
            print("\t" + _("Some jobs could not be parsed correctly"))
            # TRANSLATORS: please don't translate `manage.py validate`
            print("\t" + _("Please run `manage.py validate` for details"))
        print(_("[White Lists]"))
        try:
            whitelist_list = provider.get_builtin_whitelists()
        except RFC822SyntaxError as exc:
            print("{}:{}: {}".format(
                os.path.relpath(exc.filename, self.definition.location),
                exc.lineno, exc.msg))
            print(_("Errors prevent whitelists from being displayed"))
        else:
            for whitelist in whitelist_list:
                # TRANSLATORS: the fields are as follows:
                # 0: whitelist name
                # 1: pathname of the file the whitelist is defined in
                print("\t" + _("{0!a}, from {1}").format(
                    whitelist.name,
                    whitelist.origin.relative_to(self.definition.location)))


@docstring(
    # TRANSLATORS: please leave various options (both long and short forms),
    # environment variables and paths in their original form. Also keep the
    # special @EPILOG@ string. The first line of the translation is special and
    # is used as the help message. Please keep the pseudo-statement form and
    # don't finish the sentence with a dot. Pay extra attention to whitespace.
    # It must be correctly preserved or the result won't work. In particular
    # the leading whitespace *must* be preserved and *must* have the same
    # length on each line.
    N_("""
    perform various static analysis and validation

    This command inspects all of the jobs defined in the provider associated
    with the ``manage.py`` script. It checks for both syntax issues and
    semantic issues. Anything reported as incorrect will likely result in a
    run-time failure.

    @EPILOG@

    Refer to the online documentation for plainbox to understand how correct
    job definitions look like and how to resolve problems reported by
    ``verify``.

    The exit code can be used to determine if there were any failures. If you
    have any, ``manage.py validate`` is something that could run in a CI loop.
    """))
class ValidateCommand(ManageCommand):

    def register_parser(self, subparsers):
        """
        Overridden method of CommandBase.

        :param subparsers:
            The argparse subparsers objects in which command line argument
            specification should be created.

        This method is invoked by the command line handling code to register
        arguments specific to this sub-command. It must also register itself as
        the command class with the ``command`` default.
        """
        self.add_subcommand(subparsers)

    def get_job_list(self, provider):
        job_list, problem_list = provider.load_all_jobs()
        if problem_list:
            for exc in problem_list:
                if isinstance(exc, RFC822SyntaxError):
                    print("{}:{}: {}".format(
                        os.path.relpath(exc.filename, provider.base_dir),
                        exc.lineno, exc.msg))
                else:
                    print("{}".format(exc))
            print(_("NOTE: subsequent jobs from problematic"
                    " files are ignored"))
        return job_list

    def validate_jobs(self, job_list):
        problem_list = []
        for job in job_list:
            try:
                job.validate()
            except JobValidationError as exc:
                problem_list.append((job, exc))
        return problem_list

    def invoked(self, ns):
        provider = self.get_provider()
        job_list = self.get_job_list(provider)
        problem_list = self.validate_jobs(job_list)
        explain = {
            Problem.missing: _("missing definition of required field"),
            Problem.wrong: _("incorrect value supplied"),
            Problem.useless: _("useless field in this context"),
        }
        for job, error in problem_list:
            if isinstance(error, JobValidationError):
                # TRANSLATORS: fields are as follows:
                # 0: filename with job definition
                # 1: job id
                # 2: field name
                # 3: explanation of the problem
                print(_("{0}: job {1!a}, field {2!a}: {3}").format(
                    job.origin.relative_to(self.definition.location),
                    job.id, error.field.name, explain[error.problem]))
                # If this is a "wrong value" problem then perhaps we can
                # suggest the set of acceptable values? Those may be stored as
                # $field.symbols, though as of this writing that is only true
                # for the 'plugin' field.
                field_prop = getattr(JobDefinition, str(error.field))
                if (error.problem == Problem.wrong
                        and hasattr(field_prop, "get_all_symbols")):
                    symbol_list = field_prop.get_all_symbols()
                    print(_("allowed values are: {0}").format(
                        ', '.join(str(symbol) for symbol in symbol_list)))
            else:
                print(str(error))
        if problem_list:
            return 1
        else:
            print(_("All jobs seem to be valid"))


@docstring(
    # TRANSLATORS: please leave various options (both long and short forms),
    # environment variables and paths in their original form. Also keep the
    # special @EPILOG@ string. The first line of the translation is special and
    # is used as the help message. Please keep the pseudo-statement form and
    # don't finish the sentence with a dot. Pay extra attention to whitespace.
    # It must be correctly preserved or the result won't work. In particular
    # the leading whitespace *must* be preserved and *must* have the same
    # length on each line.
    N_("""
    update, merge and build translation catalogs

    This command exposes facilities for updating, merging and building
    message translation catalogs.
    """))
class I18NCommand(ManageCommand):

    def register_parser(self, subparsers):
        """
        Overridden method of CommandBase.

        :param subparsers:
            The argparse subparsers objects in which command line argument
            specification should be created.

        This method is invoked by the command line handling code to register
        arguments specific to this sub-command. It must also register itself as
        the command class with the ``command`` default.
        """
        parser = self.add_subcommand(subparsers)
        parser.add_argument(
            "-n", "--dry-run", default=False, action="store_true",
            help=_("don't actually do anything"))
        group = parser.add_argument_group(title=_("actions to perform"))
        group.add_argument(
            "--dont-update-pot", default=False, action="store_false",
            help=_("do not update the translation template"))
        group.add_argument(
            "--dont-merge-po", default=False, action="store_true",
            help=_("do not merge translation files with the template"))
        group.add_argument(
            "--dont-build-mo", default=False, action="store_true",
            help=_("do not build binary translation files"))

    def invoked(self, ns):
        if self.definition.gettext_domain is Unset:
            print("This provider doesn't define gettext_domain.")
            print("Add it to manage.py and try again")
            return 1
        # Create the po/ directory if needed
        if not os.path.exists(self.po_dir):
            os.makedirs(self.po_dir)
        # First update / generate the template
        if not ns.dont_update_pot:
            self._update_pot(ns.dry_run)
        # Then merge all of the po files with the new template
        if not ns.dont_merge_po:
            self._merge_po(ns.dry_run)
        # Then build all of the .mo files from each of the .po files
        if not ns.dont_build_mo:
            self._build_mo(ns.dry_run)

    @property
    def po_dir(self):
        return os.path.join(self.definition.location, 'po')

    def mo_dir(self, lang):
        return os.path.join(
            self.definition.location, 'build', 'mo', lang, 'LC_MESSAGES')

    def _update_pot(self, dry_run):
        self._cmd([
            'intltool-update',
            '--gettext-package={}'.format(self.definition.gettext_domain),
            '--pot',
        ], self.po_dir, dry_run)

    def _merge_po(self, dry_run):
        for item in os.listdir(self.po_dir):
            if not item.endswith('.po'):
                continue
            lang = os.path.splitext(item)[0]
            mo_dir = self.mo_dir(lang)
            os.makedirs(mo_dir, exist_ok=True)
            self._cmd([
                'intltool-update',
                '--gettext-package={}'.format(self.definition.gettext_domain),
                '--dist', lang
            ], self.po_dir, dry_run)

    def _build_mo(self, dry_run):
        for item in os.listdir(self.po_dir):
            if not item.endswith('.po'):
                continue
            lang = os.path.splitext(item)[0]
            mo_dir = self.mo_dir(lang)
            os.makedirs(mo_dir, exist_ok=True)
            self._cmd([
                'msgfmt',
                '{}/{}.po'.format(os.path.relpath(self.po_dir), lang),
                '-o', os.path.relpath('{}/{}.mo'.format(
                    mo_dir, self.definition.gettext_domain))
            ], None, dry_run)

    def _cmd(self, cmd, cwd, dry_run):
        if cwd is not None:
            print('(', 'cd', os.path.relpath(cwd), '&&', " ".join(cmd), ')')
        else:
            print(" ".join(cmd))
        if not dry_run:
            return subprocess.call(cmd, cwd=cwd)
        else:
            return 0


class ProviderManagerTool(ToolBase):
    """
    Command line tool that is covertly used by each provider's manage.py script

    This tool is a typical plainbox command line tool with a few sub-commands.
    There are separate sub-commands for certain key activities related to
    providers, those are:

    `manage.py info`:
        This command loads and validates the provider at a basic level.
        It displays the essential meta-data followed by a list of all the
        jobs and whitelists.

    `manage.py validate`:
        This command loads the provider and performs basic job validation,
        looking at each job definition and ensuring it could be used at
        a normal test run.

    `manage.py develop`:
        This command ensures that plainbox can see this provider. It creates a
        definition file in $XDG_DATA_HOME/plainbox-providers-1/{name}.provider
        with all the meta-data and location pointing at the directory with the
        manage.py script

    `manage.py install`:
        This command installs all of the files required by this provider to
        the provided --prefix, relative to the provided --root directory. It
        can be used by installers or package build process to create final
        provider packages

    `manage.py sdist`:
        This command creates a tarball with all of the source files required
        to install this provider. It can be used to release open-source
        providers and archive them.

    `manage.py i18n`:
        This command updates, merges and builds binary versions of message
        translation catalogs. It can be used as a part of a build system, to
        standardize and facilitate providing localized test definitions.
    """

    _SUB_COMMANDS = [
        InfoCommand,
        ValidateCommand,
        DevelopCommand,
        InstallCommand,
        SourceDistributionCommand,
        I18NCommand,
    ]

    def __init__(self, definition):
        super().__init__()
        self._definition = definition

    @property
    def definition(self):
        return self._definition

    def create_parser_object(self):
        parser = argparse.ArgumentParser(
            prog=self.get_exec_name(),
            # TRANSLATORS: please keep 'manage.py', '--help', '--version'
            # untranslated. Translate only '[options]'
            usage=_("manage.py [--help] [--version] [options]"))
        parser.add_argument(
            "--version", action="version", version=self.get_exec_version(),
            help=_("show program's version number and exit"))
        return parser

    @classmethod
    def get_exec_name(cls):
        """
        Get the name of this executable
        """
        return "manage.py"

    @classmethod
    def get_exec_version(cls):
        """
        Get the version reported by this executable
        """
        return "{}.{}.{}".format(*version[:3])

    def add_subcommands(self, subparsers):
        """
        Add top-level subcommands to the argument parser.
        """
        for cmd_cls in self._SUB_COMMANDS:
            cmd_cls(self.definition).register_parser(subparsers)

    def get_gettext_domain(self):
        return "plainbox"

    def get_locale_dir(self):
        return os.getenv("PLAINBOX_LOCALE_DIR", None)


def setup(**kwargs):
    """
    The setup method that is being called from generated manage.py scripts.

    This setup method is similar in spirit to the setup.py's setup() call
    present in most python projects. It takes any keyword arguments and tries
    to make the best of it.

    :param kwargs:
        arbitrary keyword arguments, see below for what we currently look up
    :raises:
        SystemExit with the exit code of the program. This is done regardless
        of normal / abnormal termination.

    The following keyword parameters are supported:

        name:
            name of the provider (IQN compatible). Typically something like
            ``2013.org.example:some-name`` where the ``some-name`` is a simple
            identifier and a private namespace for whoever owned
            ``org.example`` in ``2013``

        version:
            version string, required

        description:
            description (may be long/multi line), optional

        gettext_domain:
            gettext translation domain for job definition strings, optional
    """
    setup_logging()
    manage_py = inspect.stack()[1][0].f_globals['__file__']
    location = os.path.dirname(os.path.abspath(manage_py))
    definition = Provider1Definition()
    try:
        definition.location = location
        definition.name = kwargs.get('name', None)
        definition.version = kwargs.get('version', None)
        definition.description = kwargs.get('description', None)
        definition.gettext_domain = kwargs.get('gettext_domain', Unset)
    except ConfigValidationError as exc:
        raise SystemExit(_("{}: bad value of {!r}, {}").format(
            manage_py, exc.variable.name, exc.message))
    else:
        raise SystemExit(ProviderManagerTool(definition).main())
