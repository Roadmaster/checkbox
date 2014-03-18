/*
 * This file is part of Checkbox
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


Page {
    id: welcomePage
    title: settings.value("welcome/title", i18n.tr("System Testing"));

    tools: ToolbarItems {
        locked: true
        opened: false
    }

    Image {
        id: logo
        anchors {
            horizontalCenter: parent.horizontalCenter
            margins: units.gu(2)
        }
        source:"artwork/checkbox-qt-head.png"
    }

    Rectangle {
        id: logo_extend_left
        color: "#3c3b3f" // matches the background colour of the logo
        anchors.top: logo.top
        anchors.bottom: logo.bottom
        anchors.left: parent.left
        anchors.right: logo.left
        anchors.leftMargin: units.gu(2)
    }

    Rectangle {
        id: logo_extend_right
        color: "#3c3b3f" // matches the background colour of the logo
        anchors.top: logo.top
        anchors.bottom: logo.bottom
        anchors.left: logo.right
        anchors.right: parent.right
        anchors.rightMargin: units.gu(2)
    }

    Rectangle{
        color: "white"
        clip: true
        anchors {
            left: parent.left
            right: parent.right
            top: logo.bottom
            bottom: continueButton.top
            margins: units.gu(2)
        }

        Flickable {
            id: welcomeflick
            anchors.fill: parent
            contentHeight: parent.height
            boundsBehavior: Flickable.StopAtBounds

            TextEdit{
                id: welcometext

                anchors {
                    fill: parent
                    margins: units.gu(2)
                }

                // TRANSLATORS: The <p> tags are HTML - DO NOT translate them.
                text: settings.value("welcome/text", i18n.tr("<p>Welcome to System Testing.</p><p></p><p>This program contains automated and manual tests to help you assess how well your system works with Ubuntu.</p><p></p><p>This application will step the user through these tests in a predetermined order and automatically collect both system information as well as test results. It will also prompt the user for input when manual testing is required.</p><p></p><p>The run time for the tests is determined by which tests you decide to execute. The user will have the opportunity to customize the test run based on the hardware components they are interested in and the amount of time they have available.</p><p></p><p>To begin, simply click the Continue button below and follow the onscreen instructions.</p><p></p>"))

                height: units.gu(60)
                width: units.gu(30)
                cursorVisible : true
                readOnly: true
                selectByMouse : true
                textFormat: TextEdit.AutoText
                wrapMode: TextEdit.Wrap
                color: "black"
                selectedTextColor: Theme.palette.selected.foregroundText
                selectionColor: Theme.palette.selected.foreground
                font.pixelSize: FontUtils.sizeToPixels("medium")

                onLinkActivated:  {
                    cmdTool.exec("xdg-open", link)
                }
            }
        }

        Scrollbar {
            flickableItem: welcomeflick
            align: Qt.AlignTrailing
        }
    }

    Button {
        id: continueButton
        anchors{
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: units.gu(2)
        }

        text: i18n.tr("Continue")
        color: UbuntuColors.lightAubergine
        onClicked: {
            // Move to the whitelist selection screen
            mainView.state = "SUITESELECTION"
        }
    }
}
