#
# This file is part of Checkbox.
#
# Copyright 2012 Canonical Ltd.
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
from io import StringIO

from unittest import TestCase

from checkbox.parsers.efi import EfiParser


class EfiResult:

    def __init__(self):
        self.device = None

    def setEfiDevice(self, device):
        self.device = device


class TestCputableParser(TestCase):

    def getParser(self, string):
        stream = StringIO(string)
        return EfiParser(stream)

    def getResult(self, string):
        parser = self.getParser(string)
        result = EfiResult()
        parser.run(result)
        return result

    def test_empty(self):
        result = self.getResult("")
        self.assertEquals(result.device, None)

    def test_product(self):
        result = self.getResult("""
Foo Bar
""")
        self.assertEquals(result.device.vendor, None)
        self.assertEquals(result.device.product, "Foo Bar")

    def test_vendor_product(self):
        result = self.getResult("""
Foo by Bar
""")
        self.assertEquals(result.device.vendor, "Foo")
        self.assertEquals(result.device.product, "Bar")
