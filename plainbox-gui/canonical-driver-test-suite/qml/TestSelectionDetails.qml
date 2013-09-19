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

Item {
    id: testseldetails
    property var testItem;
    property bool showDetails;
    property int openHeight: units.gu(17)

    height:detailsFlick.height + detailsItem.height

    // Open/Shut label + icon
    Item {
        id: detailsItem
        height: detailsLabel.height
        width: parent.width

        anchors.bottom: detailsFlick.top

        // Initially zero as the details box is closed
        anchors.bottomMargin: 0

        Label {
            id: detailsLabel
            text: i18n.tr("Test Details")
            anchors {
                horizontalCenter: parent.horizontalCenter
            }
        }

        Image {
            id: progressIcon
            source: "artwork/UpArrow.png"
            anchors {
                left: detailsLabel.right
                leftMargin: units.gu(2)
            }
        }

        Image {
            id: progressIcon2
            source: "artwork/UpArrow.png"
            anchors {
                right: detailsLabel.left
                rightMargin: units.gu(2)
            }
        }

        MouseArea {
            anchors.fill: detailsItem
            onClicked: {showDetails = !showDetails}
        }
    }

    // Right side of the details
    Flickable {
        id: detailsFlick
        anchors.bottom: parent.bottom

        anchors.left: parent.left
        anchors.leftMargin: units.gu(2)

        anchors.right: parent.right
        anchors.rightMargin: units.gu(2)

        height: 0  // initialize to closed

        contentHeight: detailsblock.height
        clip: true
        boundsBehavior : Flickable.StopAtBounds

        Rectangle {
            id: rightRect
            anchors.right: parent.right
            anchors.top: parent.top

            height: detailsblock.height
            width: parent.width
            border{
                color: "black"
                width: 1
            }

            Item{
                id: detailsblock

                height: nameText.height + descriptionText.height + dependsText.height + requiresText.height + commandText.height + units.gu(1)
                width: parent.width

                TestSelectionDetailsItems{
                    id: nameText
                    labelName: i18n.tr("name:")
                    anchors.top: parent.top
                }

                TestSelectionDetailsItems{
                    id: descriptionText
                    labelName: i18n.tr("description:")
                    anchors.top: nameText.bottom
                }

                TestSelectionDetailsItems{
                    id: dependsText
                    labelName: i18n.tr("depends:")
                    anchors.top: descriptionText.bottom
                }

                TestSelectionDetailsItems{
                    id: requiresText
                    labelName: i18n.tr("requires:")
                    anchors.top: dependsText.bottom
                }

                TestSelectionDetailsItems{
                    id: commandText
                    labelName: i18n.tr("command:")
                    anchors.top: requiresText.bottom
                }
            }
        }
    }

    Scrollbar {
        flickableItem: detailsFlick
        align: Qt.AlignTrailing
    }

    // Update the details
    onTestItemChanged: {
        nameText.text = testItem.testname;
        descriptionText.text = testItem.description;
        dependsText.text = testItem.depends;
        requiresText.text = testItem.requires;
        commandText.text = testItem.command;
    }

    // Expand/Collapse the details
    onShowDetailsChanged:{
        if (showDetails){
            progressIcon.source = "artwork/DownArrow.png";
            progressIcon2.source = "artwork/DownArrow.png";
            detailsFlick.height = openHeight

            // We need to be spaced away from the details box
            detailsItem.anchors.bottomMargin = 2
        }
        else{
            progressIcon.source = "artwork/UpArrow.png";
            progressIcon2.source = "artwork/UpArrow.png";
            detailsFlick.height = 0

            // We dont need any margin from the details box as its closed
            detailsItem.anchors.bottomMargin = 0
        }

        // for laying out of items in which we are included
        testseldetails.height = detailsFlick.height + detailsLabel.height
    }
}
