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




Page {
    title: i18n.tr("Suite Selection")

    Item {
        id: filler
        height: units.gu(4)
    }

    Rectangle {
        id: suitelist
        width: parent.width - units.gu(4)
        color: "white"
        height: parent.height - filler.height - okbutton.height - units.gu(6)
        anchors{
            horizontalCenter: parent.horizontalCenter
            top: filler.bottom
        }

        ListView {
            id: testselection
            height: parent.height
            width: parent.width
            anchors.fill: parent
            contentHeight: units.gu(12) * testSuiteModel.count
            interactive: true
            clip: true
            boundsBehavior : Flickable.StopAtBounds
            model: testSuiteModel

            delegate: Item {}

            section {
                property: "group"
                criteria: ViewSection.FullString
                delegate: SuiteSelectionDelegate{

                    onSelectSuite: {
                    // In the model, select all tests in the suite
                    for (var i = testSuiteModel.count - 1; i >= 0; i--){
                        var item = testSuiteModel.get(i);
                        if (item.group === suite)
                            testSuiteModel.setProperty(i, "check", sel);
                     }
                }
            }
            }
        }
        Scrollbar {
            flickableItem: testselection
            align: Qt.AlignTrailing
        }
    }


    Button {
        id: okbutton
        width: units.gu(20)
        anchors {
            horizontalCenter:parent.horizontalCenter
            bottom: parent.bottom
            margins: units.gu(2)
        }
        text: i18n.tr("OK")
        color: UbuntuColors.lightAubergine
        onClicked: {mainView.state = "TESTSELECTION"}
    }

}
