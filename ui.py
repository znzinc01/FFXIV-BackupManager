import wx
from wx.lib.pubsub import pub
import wx.lib.agw.hyperlink as hl
import os
import locale
import json

import core


def UpdateSettings(settings_dict):
    with open("./resource/settings.json", "w") as file:
        write_string = json.dumps(settings_dict, indent=2, ensure_ascii=False)
        file.write(write_string)


try:
    # Read Settings File
    with open("./resource/settings.json") as settings_file:
        settings = json.loads(settings_file.read())
    default_settings = {"general": {"first_run": 1, "locale": ""},
                        "recent": {"ffxiv_data_folder": "", "backup_destination": ""}
                       }

    # Read locale from settings
    if not settings["general"]["locale"]:
        current_locale = locale.getdefaultlocale()[0]
        settings["general"]["locale"] = current_locale
        UpdateSettings(settings)
    else:
        current_locale = settings["general"]["locale"]
    locale_list = [x[:-5] for x in os.listdir("./resource") if (x.endswith(".json") and not x == "settings.json")]

    # Set locale
    if current_locale in locale_list:
        locale_json = "./resource/{}.json".format(current_locale)
    else:
        locale_json = "./resource/en_US.json"
    with open(locale_json, "r", encoding="UTF8") as locale_file:
        strings = json.loads(locale_file.read())

    # Set paths
    user_path = os.path.expanduser("~")
    app_path = os.path.dirname(os.path.abspath(__file__))
    if not settings["recent"]["ffxiv_data_folder"]:
        default_ffxiv_path = os.path.join(user_path, "Documents\My Games\FINAL FANTASY XIV - KOREA")
        if not os.path.exists(default_ffxiv_path):
            default_ffxiv_path = os.path.join(user_path, "Documents\My Games\FINAL FANTASY XIV - A Realm Reborn")
            if not os.path.exists(default_ffxiv_path):
                default_ffxiv_path = os.path.join(user_path, "Documents")
    else:
        default_ffxiv_path = settings["recent"]["ffxiv_data_folder"]

    if not settings["recent"]["backup_destination"]:
        default_backup_path = app_path
    else:
        default_backup_path = settings["recent"]["backup_destination"]


except Exception as e:
    tmp = wx.App()
    wx.MessageBox("Cannot start FFXIV-BackupManager:\n{}".format(e), "FFXIV-BackupManager",
                  wx.OK | wx.ICON_EXCLAMATION)
    exit(0)


class BackupTab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        source_label = wx.StaticText(self, -1, strings["ffxiv_data_folder"])
        self.sourceText = wx.TextCtrl(self, -1, default_ffxiv_path, size=(500, -1), style=wx.TE_READONLY)
        self.browseFFXIVButton = wx.Button(self, -1, strings["browse"])
        self.Bind(wx.EVT_BUTTON, self.OnClickBrowseFFXIVButton, self.browseFFXIVButton)

        dest_label = wx.StaticText(self, -1, strings["backup_folder"])
        self.destText = wx.TextCtrl(self, -1, default_backup_path, size=(500, -1), style=wx.TE_READONLY)
        self.browseDestButton = wx.Button(self, -1, strings["browse"])
        self.Bind(wx.EVT_BUTTON, self.OnClickBrowseDestButton, self.browseDestButton)

        self.backupButton = wx.Button(self, -1, strings["backup"])
        self.Bind(wx.EVT_BUTTON, self.OnClickBackupButton, self.backupButton)
        
        sizer = wx.FlexGridSizer(cols=4, hgap=6, vgap=6)
        sizer.AddMany([
            wx.StaticText(self, size=(20, 10)), wx.StaticText(self), wx.StaticText(self), wx.StaticText(self),
            wx.StaticText(self), source_label, self.sourceText, self.browseFFXIVButton,
            wx.StaticText(self), dest_label, self.destText, self.browseDestButton,
            wx.StaticText(self), wx.StaticText(self), wx.StaticText(self), self.backupButton])
        self.SetSizer(sizer)

    def OnClickBrowseFFXIVButton(self, event):
        dialog = wx.DirDialog(None, strings["choose_ffxiv_data_folder"], default_ffxiv_path,
                              wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.sourceText.SetValue(dialog.GetPath())
            status_message = "{}: {}".format(strings["selected_ffxiv_data_folder"], dialog.GetPath())
            pub.sendMessage("change_statusbar", message=status_message)
        dialog.Destroy()

    def OnClickBrowseDestButton(self, event):
        dialog = wx.DirDialog(None, strings["choose_backup_destination"], default_backup_path,
                              wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.destText.SetValue(dialog.GetPath())
            status_message = "{}: {}".format(strings["selected_destination_folder"], dialog.GetPath())
            pub.sendMessage("change_statusbar", message=status_message)
        dialog.Destroy()

    def OnClickBackupButton(self, event):
        is_backup_success, return_string = core.backup(self.sourceText.GetValue(), self.destText.GetValue())
        if is_backup_success:
            wx.MessageBox("{}\n{}: {}".format(strings["backup_success"], strings["backup_file"],
                                              return_string), "FFXIV Backup Manager", wx.OK)
            pub.sendMessage("change_statusbar", message=strings["backup_success"])
            settings["recent"]["ffxiv_data_folder"] = self.sourceText.GetValue()
            settings["recent"]["backup_destination"] = self.destText.GetValue()
            UpdateSettings(settings)
        else:
            wx.MessageBox("{}\n{}".format(strings["backup_failed"], return_string),
                          "FFXIV Backup Manager", wx.OK)
            pub.sendMessage("change_statusbar", message="Backup Failed")


class RestoreTab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        source_label = wx.StaticText(self, -1, strings["backup_file"])
        self.sourceText = wx.TextCtrl(self, -1, "", size=(500, -1), style=wx.TE_READONLY)
        self.browseBackupButton = wx.Button(self, -1, strings["browse"])
        self.Bind(wx.EVT_BUTTON, self.OnClickBrowseBackupButton, self.browseBackupButton)

        dest_label = wx.StaticText(self, -1, strings["ffxiv_data_folder"])
        self.destText = wx.TextCtrl(self, -1, default_ffxiv_path, size=(500, -1), style=wx.TE_READONLY)
        self.browseFFXIVButton = wx.Button(self, -1, strings["browse"])
        self.Bind(wx.EVT_BUTTON, self.OnClickBrowseFFXIVButton, self.browseFFXIVButton)

        self.restoreButton = wx.Button(self, -1, strings["restore"])
        self.Bind(wx.EVT_BUTTON, self.OnClickRestoreButton, self.restoreButton)

        sizer = wx.FlexGridSizer(cols=4, hgap=6, vgap=6)
        sizer.AddMany([
            wx.StaticText(self, size=(20, 10)), wx.StaticText(self), wx.StaticText(self), wx.StaticText(self),
            wx.StaticText(self), source_label, self.sourceText, self.browseBackupButton,
            wx.StaticText(self), dest_label, self.destText, self.browseFFXIVButton,
            wx.StaticText(self), wx.StaticText(self), wx.StaticText(self), self.restoreButton])
        self.SetSizer(sizer)

    def OnClickBrowseBackupButton(self, event):
        dialog = wx.FileDialog(None, strings["choose_backup_file"], wildcard=".zip files(*.zip)|*.zip",
                               defaultDir=default_backup_path,
                               style=wx.FD_DEFAULT_STYLE | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.sourceText.SetValue(dialog.GetPath())
            status_message = "{}: {}".format(strings["selected_backup_file"],
                                             os.path.basename(os.path.normpath(dialog.GetPath())))
            pub.sendMessage("change_statusbar", message=status_message)
        dialog.Destroy()

    def OnClickBrowseFFXIVButton(self, event):
        dialog = wx.DirDialog(None, strings["choose_ffxiv_data_folder"], default_ffxiv_path,
                              wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.destText.SetValue(dialog.GetPath())
            status_message = "{}: {}".format(strings["selected_ffxiv_data_folder"], dialog.GetPath())
            pub.sendMessage("change_statusbar", message=status_message)
        dialog.Destroy()

    def OnClickRestoreButton(self, event):
        backup_file_name = os.path.basename(os.path.normpath(self.sourceText.GetValue()))
        user_confirm_dialog = wx.MessageDialog(None, "{}: {}\n{}".format(strings["selected_backup_file"],
                                                                         backup_file_name, strings["restore_warning"]),
                                               "Confirm", wx.YES_NO | wx.ICON_EXCLAMATION)
        user_confirm = user_confirm_dialog.ShowModal()
        if user_confirm == wx.ID_YES:
            is_restore_success, return_string = core.restore(self.sourceText.GetValue(), self.destText.GetValue())
            if is_restore_success:
                wx.MessageBox(strings["restore_success"], "FFXIV Backup Manager", wx.OK)
                exit(0)
            else:
                wx.MessageBox("{}\n{}".format(strings["restore_failed"], return_string),
                              "FFXIV Backup Manager", wx.OK)
                pub.sendMessage("change_statusbar", message=strings["restore_failed"])
        else:
            pub.sendMessage("change_statusbar", message=strings["restore_cancelled"])


class SettingsTab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        instructions_label = wx.StaticText(self, -1, strings["settings_instructions"])

        select_locale_label = wx.StaticText(self, -1, "Select Locale")
        self.localeSelectComboBox = wx.ComboBox(self, -1, value=settings["general"]["locale"] ,choices=locale_list, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectlocale)

        reset_label = wx.StaticText(self, -1, strings["reset_settings"])
        self.resetSettingsButton = wx.Button(self, -1, strings["reset"])
        self.Bind(wx.EVT_BUTTON, self.OnClickResetSettingsButton, self.resetSettingsButton)

        sizer = wx.FlexGridSizer(cols=4, hgap=6, vgap=6)
        sizer.AddMany([
            instructions_label, wx.StaticText(self), wx.StaticText(self),  wx.StaticText(self),
            select_locale_label, self.localeSelectComboBox, wx.StaticText(self), wx.StaticText(self),
            reset_label, self.resetSettingsButton, wx.StaticText(self), wx.StaticText(self)
        ])
        self.SetSizer(sizer)

    def OnClickResetSettingsButton(self, event):
        user_confirm_dialog = wx.MessageDialog(None, "{}".format(strings["reset_warning"]),
                                               "Confirm", wx.YES_NO | wx.ICON_EXCLAMATION)
        user_confirm = user_confirm_dialog.ShowModal()
        if user_confirm == wx.ID_YES:
            try:
                settings = default_settings
                UpdateSettings(settings)
                wx.MessageBox(strings["reset_success"], "FFXIV Backup Manager", wx.OK)
                pub.sendMessage("close_app")
            except Exception as e:
                wx.MessageBox("{}\n{}".format(strings["restore_failed"], e),
                              "FFXIV Backup Manager", wx.OK)
                pub.sendMessage("change_statusbar", message=strings["reset_failed"])
        else:
            pass

    def OnSelectlocale(self, event):
        selected = self.localeSelectComboBox.GetValue()
        try:
            settings["general"]["locale"] = selected
            UpdateSettings(settings)
        except Exception as e:
            wx.MessageBox("{}\n{}".format(strings["settings_failed"], e),
                          "FFXIV Backup Manager", wx.OK)
            pub.sendMessage("change_statusbar", message=strings["settings_failed"])


class InfoTab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        version_label = wx.StaticText(self, -1, "FFXIV Backup Manager v1.0")
        sourcecode_label = hl.HyperLinkCtrl(self, -1, "View source code at Github",
                                            URL="https://github.com/znzinc01/FFXIV-BackupManager")
        twitter_label = hl.HyperLinkCtrl(self, -1, "Contact developer with Twitter",
                                            URL="https://twitter.com/znzinc01")

        sizer = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        sizer.AddMany([
            version_label, wx.StaticText(self),
            sourcecode_label, wx.StaticText(self),
            twitter_label, wx.StaticText(self)
        ])
        self.SetSizer(sizer)


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "FFXIV Backup Manager",
                          size=(800, 220),
                          style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)
        p = wx.Panel(self, -1)
        nb = wx.Notebook(p)

        backuptab = BackupTab(nb)
        restoretab = RestoreTab(nb)
        settingstab = SettingsTab(nb)
        infotab = InfoTab(nb)
        nb.AddPage(backuptab, strings["backup"])
        nb.AddPage(restoretab, strings["restore"])
        nb.AddPage(settingstab, strings["settings"])
        nb.AddPage(infotab, strings["info"])

        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(sizer)

        pub.subscribe(self.change_statusbar, "change_statusbar")
        pub.subscribe(self.close_app, "close_app")
        self.statusbar = self.CreateStatusBar()
        self.SetStatusText("")

    def change_statusbar(self, message):
        self.SetStatusText(message)

    def close_app(self):
        self.Close()


if __name__ == "__main__":
    app = wx.App()
    if settings["general"]["first_run"]:
        settings["general"]["first_run"] = 0
        UpdateSettings(settings)
        wx.MessageBox(strings["fisrt_run_help"], "FFXIV-BackupManager",
                      wx.OK | wx.ICON_INFORMATION)
    frame = MainFrame()
    frame.SetIcon(wx.Icon("resource\\icon.ico", wx.BITMAP_TYPE_ICO))
    frame.Show()
    app.MainLoop()
