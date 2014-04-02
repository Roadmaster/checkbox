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
import Ubuntu.Components.Popups 0.1
import "."

Dialog {
    id: dialog

    title: i18n.tr("Report")
    text: settings.value("submission/message", i18n.tr("The following test report has been generated. You may view it now or save it for later."))

    TextField {
        RegExpValidator {
            id: regex_validator
            regExp: new RegExp(settings.value("submission/regex", ".*"));
        }
        function initialize() {
            var input_type = settings.value("submission/input_type", "")
            if (input_type == "regex") {
                validator = regex_validator;
                visible = true;
            }
            else if (input_type == "email") {
                inputMethodHints = Qt.ImhEmailCharactersOnly;
                visible = true;
            }
            else {
                visible = false;
            }
            var secure_id = settings.value("submission/secure_id","");
            if (secure_id) {
                text = secure_id;
            }
        }

        id: upload_input
        placeholderText: settings.value("submission/input_placeholder", "")
        Component.onCompleted: initialize()
    }

    Row {
        function initialize() {
            if (settings.value("submission/submit_to_hexr","false").toLowerCase() == "true") {
                visible = true;
            }
        }

        spacing: units.gu(8)
        visible: false
        Label {
            id: submit_to_hexr_label
            text: i18n.tr("Submit to HEXR:")
        }

        CheckBox {
            id: submit_to_hexr
            text: i18n.tr("Submit to HEXR:")
        }
        Component.onCompleted: initialize()

    }

    Button {
        id: submitbutton
        text: settings.value("submission/ok_btn_text", "Save Results")
        enabled: upload_input.acceptableInput
        color: UbuntuColors.orange
        onClicked: {
            var submit_to = settings.value("transport/submit_to", "")
            var export_path = settings.value("exporter/xml_export_path", "")
            var option_list = new Array("client-name=" + client_name);

            if (!export_path) {
                export_path = guiEngine.GetSaveFileName();
            }
            var success = guiEngine.GuiExportSessionToFileAsXML(export_path,
                                                                option_list);
            if (submit_to == "certification") {
                if (success) {
                    dialog.text = guiEngine.SendSubmissionViaCertificationTransport(export_path,
                                                                                    upload_input.text,
                                                                                    submit_to_hexr.checked);
                }
                else {
                    dialog.text = i18n.tr("Could not export the tests results for uploading.");
                }
            }
            else {
                runmanagerview.reportIsSaved = success;
            }
        }
    }
    Button {
        id: view_button
        text: i18n.tr("View Results")
        color: UbuntuColors.lightAubergine
        onClicked: {
            onClicked:{
                var mysavepath = '/tmp/report.html';
                var option_list = new Array("client-name=" + client_name);
                runmanagerview.reportIsSaved = guiEngine.GuiExportSessionToFileAsHTML(mysavepath,
                                                                                      option_list);
                Qt.openUrlExternally(mysavepath);
            }
        }
    }
    Button {
        id: donebutton
        text: i18n.tr("Done")
        color: UbuntuColors.warmGrey
        onClicked: {
            if (!runmanagerview.reportIsSaved)
                PopupUtils.open(submission_warning_dialog, donebutton);
            else
                PopupUtils.close(dialog)
        }
    }

    Component {
        id: submission_warning_dialog
        WarningDialog{
            text: settings.value("submission/cancel_warning", i18n.tr("You are about to exit this test run without saving your results report.  Do you want to save the report?"))

            showContinue: false
            showCheckbox: false

            onCancel: PopupUtils.close(dialog)
        }
    }
}
