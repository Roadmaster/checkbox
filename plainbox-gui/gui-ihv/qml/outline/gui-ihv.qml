/*
 * This file is part of plainbox-gui
 *
 * Copyright 2013 Canonical Ltd.
 *
 * Authors:
 * - Andrew Haigh <andrew.haigh@cellsoftware.co.uk>
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
import GuiEngine 1.0
import Ubuntu.Components 0.1
import Ubuntu.Components.Popups 0.1
import "."


MainView {
    id: mainView
    width: units.gu(120)
    height: units.gu(110)


    PageStack {
        id: pageStack
        state: "WELCOME"
        property string pageName: "DemoWarnings.qml"

        Component.onCompleted: {
            push(Qt.resolvedUrl(pageName))
        }

        onPageNameChanged: {
            pop();
            push(Qt.resolvedUrl(pageName))
        }
    }

    // Fill in states for all the pages.
    // The pages/views will set the state to the next one when it is dones
    // like this: onClicked: {mainView.state = "TESTSELECTION"}
    states: [
        State {
            name: "WELCOME"
            PropertyChanges { target: pageStack; pageName: "WelcomeView.qml"}
        },
        State {
            name: "DEMOWARNINGS"
            PropertyChanges { target: pageStack; pageName: "DemoWarnings.qml"}
        },
        State {
            name: "TESTSELECTION"
            PropertyChanges { target: pageStack; pageName: "TestSelectionView.qml"}
        }

    ]
}



