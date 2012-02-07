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
class DmiResult:

    def __init__(self):
        self.devices = []

    def addDmiDevice(self, device):
        self.devices.append(device)

    def getDevice(self, category):
        for device in self.devices:
            if device.category == category:
                return device

        return None


class TestDmiMixin:

    def getParser(self):
        raise NotImplementedError()

    def getResult(self):
        parser = self.getParser()
        result = DmiResult()
        parser.run(result)
        return result

    def test_devices(self):
        result = self.getResult()
        self.assertEquals(len(result.devices), 4)

    def test_bios(self):
        result = self.getResult()
        device = result.getDevice("BIOS")
        self.assertTrue(device)
        self.assertEquals(device.product, "BIOS PRODUCT")
        self.assertEquals(device.vendor, "BIOS VENDOR")
        self.assertEquals(device.serial, None)

    def test_board(self):
        result = self.getResult()
        device = result.getDevice("BOARD")
        self.assertTrue(device)
        self.assertEquals(device.product, None)
        self.assertEquals(device.vendor, None)
        self.assertEquals(device.serial, None)

    def test_chassis(self):
        result = self.getResult()
        device = result.getDevice("CHASSIS")
        self.assertTrue(device)
        self.assertEquals(device.product, "Notebook")
        self.assertEquals(device.vendor, "CHASSIS VENDOR")
        self.assertEquals(device.serial, None)

    def test_system(self):
        result = self.getResult()
        device = result.getDevice("SYSTEM")
        self.assertTrue(device)
        self.assertEquals(device.product, "SYSTEM PRODUCT")
        self.assertEquals(device.vendor, "SYSTEM VENDOR")
        self.assertEquals(device.serial, "SYSTEM SERIAL")
