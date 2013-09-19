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

Rectangle {
    id: summary

    property int totalTimeEst: 0
    property int totalTests: 6
    property int totalManualTests: 2
    property int totalImplicitTests: 999

    height: units.gu(3)
    color: "lightsteelblue"
    border {
        color: UbuntuColors.warmGrey
        width: 1
    }

    Text {
        id: estimatedTimeText
        text: i18n.tr("Total time: [~" + formatTotalTime(summary.totalTimeStr) + "]")
        color: "darkslateblue"
        anchors{
            verticalCenter: parent.verticalCenter
            left: parent.left
            leftMargin: units.gu(1)
        }
        function formatTotalTime(){
            var estTimeStr = ""
            if (totalTimeEst == 0)
                estTimeStr = i18n.tr("0");
            else if (totalTimeEst/60 < 1)
                estTimeStr = i18n.tr("< 1 minute");
            else {
                var durMinutes = Math.round(totalTimeEst/60);
                estTimeStr = durMinutes.toString() + i18n.tr(" minute");
                if (durMinutes > 1)
                    estTimeStr += 's';
            }
            return  estTimeStr;
        }
    }

    Text {
        id: totalTestsText
        text: i18n.tr("Selected : [" + summary.totalTests + "]")
        color:"darkslateblue"
        anchors{
            verticalCenter: parent.verticalCenter
            left: estimatedTimeText.right
            leftMargin: units.gu(4)
        }
    }

    Text {
        id: manualTestsText
        text: i18n.tr("Manual : [" + summary.totalManualTests + "]")
        color: "darkslateblue"
        anchors{
            verticalCenter: parent.verticalCenter
            left: totalTestsText.right
            leftMargin: units.gu(4)
        }
    }

    Text {
        id: implicitTestsText
        text: i18n.tr("Implicit : [" + summary.totalImplicitTests + "]")
        color: "darkslateblue"
        anchors{
            verticalCenter: parent.verticalCenter
            left: manualTestsText.right
            leftMargin: units.gu(4)
        }
    }

    Text {
        id: totalAllTestsText
        text: i18n.tr("Total : [" + (parseInt(summary.totalTests) + parseInt(summary.totalImplicitTests)) + "]")
        color: "darkslateblue"
        anchors{
            verticalCenter: parent.verticalCenter
            left: implicitTestsText.right
            leftMargin: units.gu(4)
        }
    }
}
