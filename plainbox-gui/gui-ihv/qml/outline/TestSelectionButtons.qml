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



Row {
    id: bottombuttons

    signal selectAll
    signal deselectAll
    signal startTesting


    width: parent.width - units.gu(20)
    spacing: (parent.width - (units.gu(18)*3))/3

    Button {
         id:selectButton
         text: i18n.tr("Select All")
         color: UbuntuColors.warmGrey
         width: units.gu(18)
         onClicked: {
             bottombuttons.selectAll();
         }
    }
    Button {
         id: deselectButton
         text: i18n.tr("Deselect All")
         color: UbuntuColors.warmGrey
         width: units.gu(18)
         onClicked:{
             bottombuttons.deselectAll();
         }

    }
    Button {
        id: startTesting
        text: i18n.tr("Start Testing")
        color: UbuntuColors.lightAubergine
        width: units.gu(18)
        onClicked:{
            bottombuttons.startTesting();
        }
    }


}
