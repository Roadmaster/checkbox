#
# Copyright (c) 2008 Canonical
#
# Written by Marc Tardif <marc@interunion.ca>
#
# This file is part of HWTest.
#
# HWTest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HWTest is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HWTest.  If not, see <http://www.gnu.org/licenses/>.
#
import unittest

from xml.dom.minidom import Document

from hwtest.report import ReportManager, Report


class StubReport(Report):

    def register_dumps(self):
        self._manager.handle_dumps(str, self.dumps_test)

    def register_loads(self):
        self._manager.handle_loads("test", self.loads_test)

    def dumps_test(self, obj, parent):
        text_node = self._manager.document.createTextNode(obj)
        parent.appendChild(text_node)

    def loads_test(self, node):
        return node.childNodes[0].nodeValue.strip()

class ReportManagerTest(unittest.TestCase):

    name = "test"

    def create_element(self, name):
        document = Document()
        element = document.createElement(name)
        document.appendChild(element)
        return element

    def create_text_node(self, name, text):
        element = self.create_element(name)
        text_node = element.createTextNode(text)
        element.appendChild(text_node)
        return text_node

    def test_constructor(self):
        rm = ReportManager(self.name)
        self.assertTrue(rm.name == self.name)

    def test_handle_dumps(self):
        rm = ReportManager(self.name)

        str_func = lambda obj, parent: "str"
        rm.handle_dumps(str, str_func)
        self.assertTrue(rm.call_dumps("test1", None) == "str")

        int_func = lambda obj, parent: "int"
        rm.handle_dumps(int, int_func)
        self.assertTrue(rm.call_dumps(1, None) == "int")
        self.assertTrue(rm.call_dumps("test2", None) == "str")

    def test_handle_loads(self):
        rm = ReportManager(self.name)

        bar_func = lambda node: "bar"
        foo_element = self.create_element("foo")
        rm.handle_loads("foo", bar_func)
        self.assertTrue(rm.call_loads(foo_element) == "bar")

        baz_func = lambda node: "baz"
        bar_element = self.create_element("bar")
        rm.handle_loads("bar", baz_func)
        self.assertTrue(rm.call_loads(bar_element) == "baz")
        self.assertTrue(rm.call_loads(foo_element) == "bar")

    def test_handle_dumps_and_loads(self):
        rm = ReportManager(self.name)
        rm.add(StubReport())

        document = rm.dumps("test1")
        str = document.toprettyxml("")
        self.assertTrue("test1" in str)

        data = rm.loads(str)
        self.assertTrue(data.has_key("test"))
        self.assertTrue(data["test"] == "test1")
