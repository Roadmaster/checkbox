/*
 * This file is part of plainbox-gui
 *
 * Copyright 2013 Canonical Ltd.
 *
 * Authors:
 * - Julia Segal <julia.segal@cellsoftware.co.uk>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */


import QtQuick 2.0
import Ubuntu.Components 0.1
import Ubuntu.Components.ListItems 0.1 as ListItem
import "."

Rectangle {
    color: "white"
    height: parent.height

    SuiteListModel{
        id: suiteModel
    }

    Flickable {
        id: listflick
        anchors.fill: parent
        height: parent.height
        width: parent.width
        clip: true
        contentHeight: groupedList.height
        boundsBehavior : Flickable.StopAtBounds


        ListView {
            id: groupedList
            model: testSuiteModel
            width: parent.width
            height: units.gu(8) * groupedList.count + units.gu(10)
            interactive: false


            delegate:  ListItem.Standard {
                text: i18n.tr("       " + testname)
                control: CheckBox {
                    anchors.verticalCenter: parent.verticalCenter
                    checked: true
                }

            }

            section.property: "group"
            section.criteria: ViewSection.FullString
            section.delegate: ListItem.Standard {
                text: i18n.tr(section)
                control: CheckBox {
                    anchors.verticalCenter: parent.verticalCenter
                    checked: true
                }

            }

        }
    }

    Scrollbar {
        flickableItem: listflick
        align: Qt.AlignTrailing
    }

}


