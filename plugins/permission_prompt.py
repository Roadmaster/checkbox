#
# Copyright (c) 2008 Canonical
#
# Written by Marc Tardif <marc@interunion.ca>
#
# This file is part of Checkbox.
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
#
import os

from gettext import gettext as _

from checkbox.plugin import Plugin


class PermissionPrompt(Plugin):

    def register(self, manager):
        super(PermissionPrompt, self).register(manager)
        self._manager.reactor.call_on("prompt-begin", self.prompt_begin)

    def prompt_begin(self, interface):
        if os.getuid() != 0:
            self._manager.reactor.fire("prompt-error", interface,
                _("Administrator Access Needed"),
                _("You need to be an administrator to use this application."))
            self._manager.reactor.stop_all()


factory = PermissionPrompt
