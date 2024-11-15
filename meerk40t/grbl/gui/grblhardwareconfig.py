#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 1.0.5 on Mon Nov 13 07:33:41 2023
#


import wx

from meerk40t.grbl.controller import hardware_settings
from meerk40t.gui.icons import icons8_curly_brackets
from meerk40t.gui.mwindow import MWindow
from meerk40t.gui.wxutils import EditableListCtrl, ScrolledPanel, wxButton
from meerk40t.kernel import signal_listener

_ = wx.GetTranslation


class GrblIoButtons(wx.Panel):
    def __init__(self, *args, context=None, chart=None, **kwds):
        self.service = context
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)
        self.service.themes.set_window_colors(self)
        self.chart = chart

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        self.button_refresh = wxButton(self, wx.ID_ANY, _("Refresh"))
        sizer_2.Add(self.button_refresh, 0, wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.on_button_refresh, self.button_refresh)

        self.button_write = wxButton(self, wx.ID_ANY, _("Write"))
        sizer_2.Add(self.button_write, 0, wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.on_button_write, self.button_write)

        self.button_export = wxButton(self, wx.ID_ANY, _("Export"))
        self.button_export.SetToolTip(_("Export Settings"))
        self.button_write.SetToolTip(_("This will write settings to hardware."))
        self.button_refresh.SetToolTip(_("Reread settings from hardware."))
        sizer_2.Add(self.button_export, 0, wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.on_button_export, self.button_export)

        self.SetSizer(sizer_2)

    def on_button_refresh(self, event):
        self.service("gcode $$\n")

    def on_button_write(self, event):
        chart = self.chart.chart
        count = chart.GetItemCount()
        eeprom_writes = []
        for i in range(count):
            setting = chart.GetItemText(i)
            if len(setting) < 2:
                continue
            hardware_index = int(setting[1:])
            d = hardware_settings(hardware_index)
            try:
                value = float(chart.GetItemText(i, 2))
            except ValueError:
                continue
            if d[-1] == int:
                value = int(value)
            if value != self.service.hardware_config.get(hardware_index):
                eeprom_writes.append(f"${hardware_index}={value}")
        if eeprom_writes:
            dlg = wx.MessageDialog(
                self,
                _("This will write settings to hardware.")
                + "\n"
                + "\n".join(eeprom_writes),
                _("Are you sure?"),
                wx.YES_NO | wx.ICON_WARNING,
            )
            dlgresult = dlg.ShowModal()
            dlg.Destroy()
            if dlgresult != wx.ID_YES:
                return
            for ew in eeprom_writes:
                self.service(f".gcode {ew}")
            self.service(".gcode $$")

    def on_button_export(self, event):
        filetype = "*.nc"
        with wx.FileDialog(
            self.service.root.gui,
            _("Export Settings"),
            wildcard=filetype,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            if not pathname.lower().endswith(".nc"):
                pathname += ".nc"
        chart = self.chart.chart
        with open(pathname, "w") as f:
            count = chart.GetItemCount()
            for i in range(count):
                setting = chart.GetItemText(i)
                value = chart.GetItemText(i, 2)
                if chart.GetItemText(i, 3) in ("bitmask", "boolean"):
                    try:
                        value = int(float(value))
                    except ValueError:
                        continue
                f.write(f"{setting}={value}\n")


class GrblHardwareProperties(ScrolledPanel):
    def __init__(self, *args, context=None, **kwds):
        self.service = context
        kwds["style"] = kwds.get("style", 0)
        ScrolledPanel.__init__(self, *args, **kwds)
        if context is not None:
            context.themes.set_window_colors(self)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        chart = EditableListCtrl(
            self,
            wx.ID_ANY,
            style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES | wx.LC_SINGLE_SEL,
        )
        self.chart = chart
        self.build_columns()
        self.fill_chart()

        chart.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.on_label_start_edit)
        chart.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_label_end_edit)

        sizer_1.Add(self.chart, 1, wx.EXPAND, 0)

        self.io_panel = GrblIoButtons(self, wx.ID_ANY, context=self.service, chart=self)
        sizer_1.Add(self.io_panel, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)

    def build_columns(self):
        chart = self.chart
        for column, width in (
            ("$#", 60),
            ("Parameter", 200),
            ("Value", 100),
            ("Unit", 100),
            ("Description", 1000),
        ):
            chart.AppendColumn(
                column,
                format=wx.LIST_FORMAT_LEFT,
                width=width,
            )
        chart.resize_columns()

    def fill_chart(self):
        chart = self.chart
        chart.DeleteAllItems()
        settings = hardware_settings
        for i in range(200):
            d = settings(i)
            if d is None:
                continue
            ignore, parameter, units, data_type = d
            value = ""
            if i in self.service.hardware_config:
                try:
                    value = str(data_type(self.service.hardware_config[i]))
                except ValueError:
                    # data_type could not be used to cast the value.
                    pass

            row_id = chart.InsertItem(chart.GetItemCount(), f"${i}")
            chart.SetItem(row_id, 1, str(parameter))
            chart.SetItem(row_id, 2, str(value))
            chart.SetItem(row_id, 3, str(units))
            chart.SetItem(row_id, 4, str(parameter.upper()))

    def on_label_start_edit(self, event):
        col_id = event.GetColumn()  # Get the current column
        if col_id == 2:
            event.Allow()
        else:
            event.Veto()

    def on_label_end_edit(self, event):
        row_id = event.GetIndex()  # Get the current row
        col_id = event.GetColumn()  # Get the current column
        new_data = event.GetLabel()  # Get the changed data
        # Validate
        v = self.chart.GetItemText(row_id, 0)
        try:
            v = int(v[1:])
            settings = hardware_settings(v)
            if settings:
                ignore, parameter, units, data_type = settings
                new_data = str(data_type(new_data))
        except ValueError:
            event.Veto()
            return
        self.chart.SetItem(row_id, col_id, new_data)

    @signal_listener("grbl:hwsettings")
    def hardware_settings_changed(self, origin, *args):
        self.fill_chart()

    def pane_show(self):
        pass

    def pane_hide(self):
        return


# end of class GrblHardwareProperties


class GRBLHardwareConfig(MWindow):
    def __init__(self, *args, **kwds):
        super().__init__(1000, 500, *args, **kwds)
        self.service = self.context.device
        self.SetTitle(_("GRBL Hardware Config"))
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(icons8_curly_brackets.GetBitmap())
        self.SetIcon(_icon)
        self.SetHelpText("grblhwconfig")

        self.hw_panel = GrblHardwareProperties(self, wx.ID_ANY, context=self.service)
        self.sizer.Add(self.hw_panel, 1, wx.EXPAND, 0)
        self.Layout()
        self.restore_aspect()
        self._opened_port = None

    def window_open(self):
        self.hw_panel.pane_show()

    def window_close(self):
        self.hw_panel.pane_hide()

    def delegates(self):
        yield self.hw_panel

    @staticmethod
    def submenu():
        return "Device-Settings", "GRBL Hardware Config"
