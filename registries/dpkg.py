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
import re

from checkbox.registries.command import CommandRegistry


class DpkgRegistry(CommandRegistry):
    """Registry for dpkg information.

    For the moment, this registry only contains items for the version
    and architecture as returned by the dpkg command.
    """

    def items(self):
        items = []
        match = re.search(r"([\d\.]+) \((.*)\)", str(self))
        items.append(("version", match.group(1)))
        items.append(("architecture", match.group(2)))

        return items


factory = DpkgRegistry
