from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager import PluginBase
from src.backend.PluginManager.ActionBase import ActionBase

# Import python modules
import os
from enum import Enum

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger as log

class TextOptions(Enum):
    TRACK_NAME = "track_name"
    ARTIST_NAME = "artist_name"
    ALBUM_NAME = "album_name"
    DEVICE_NAME = "device_name"
    VOLUME = "volume"
    NONE = "none"

class Texts(Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"

class ActionSettings(ActionBase):

    text_settings = {
        TextOptions.TRACK_NAME: "",
        TextOptions.ARTIST_NAME: "",
        TextOptions.ALBUM_NAME: "",
        TextOptions.DEVICE_NAME: "",
        TextOptions.VOLUME: "",
        TextOptions.NONE: ""
    }

    top_text_setting = ""
    middle_text_setting = ""
    bottom_text_setting = ""

    backend = None

    internal_settings = {}

    def __init__(self, actionName: str, backend: any):
        self.actionName = actionName
        self.backend = backend

        self.top_text_setting = self.text_settings[TextOptions.NONE]
        self.middle_text_setting = self.text_settings[TextOptions.NONE]
        self.bottom_text_setting = self.text_settings[TextOptions.NONE]

        self.text_settings = {
            TextOptions.TRACK_NAME: "Track Name",
            TextOptions.ARTIST_NAME: "Artist Name",
            TextOptions.ALBUM_NAME: "Album Name",
            TextOptions.DEVICE_NAME: "Device Name",
            TextOptions.VOLUME: "Volume",
            TextOptions.NONE: "None",
        }

    def get_settings(self) -> dict:
        return self.internal_settings

    def set_settings(self, settings: dict) -> None:
        self.internal_settings = settings

    def get_config_rows(self) -> list:
        rows = []

        # Create Device Selector Element
        self.devices_model = Gtk.ListStore.new([str, str])
        self.devices_select = ComboRow(model=self.devices_model,
                                        title="Select Device")

        self.device_selector_renderer = Gtk.CellRendererText()
        self.devices_select.combo_box.pack_start(self.device_selector_renderer, True)
        self.devices_select.combo_box.add_attribute(self.device_selector_renderer, "text", 0)

        self.devices_select.combo_box.connect("changed", self.on_device_select)
        rows.append(self.devices_select)

        # Create Top Row Text Selector Element
        self.Top_Text_model = Gtk.ListStore.new([str, str])
        self.Top_Text_select = ComboRow(model=self.Top_Text_model,
                                        title="Select Top Text")

        self.Top_Text_renderer = Gtk.CellRendererText()
        self.Top_Text_select.combo_box.pack_start(self.Top_Text_renderer, True)
        self.Top_Text_select.combo_box.add_attribute(self.Top_Text_renderer, "text", 0)

        self.Top_Text_select.combo_box.connect("changed", self.on_top_text_select)
        rows.append(self.Top_Text_select)

        # Create Middle Row Text Selector Element
        self.Middle_Text_model = Gtk.ListStore.new([str, str])
        self.Middle_Text_select = ComboRow(model=self.Middle_Text_model,
                                        title="Select Middle Text")

        self.Middle_Text_renderer = Gtk.CellRendererText()
        self.Middle_Text_select.combo_box.pack_start(self.Middle_Text_renderer, True)
        self.Middle_Text_select.combo_box.add_attribute(self.Middle_Text_renderer, "text", 0)

        self.Middle_Text_select.combo_box.connect("changed", self.on_middle_text_select)
        rows.append(self.Middle_Text_select)

        # Create Bottom Row Text Selector Element
        self.Bottom_Text_model = Gtk.ListStore.new([str, str])
        self.Bottom_Text_select = ComboRow(model=self.Bottom_Text_model,
                                        title="Select Bottom Text")

        self.Bottom_Text_renderer = Gtk.CellRendererText()
        self.Bottom_Text_select.combo_box.pack_start(self.Bottom_Text_renderer, True)
        self.Bottom_Text_select.combo_box.add_attribute(self.Bottom_Text_renderer, "text", 0)

        self.Bottom_Text_select.combo_box.connect("changed", self.on_bottom_text_select)
        rows.append(self.Bottom_Text_select)

        self.set_settings_defaults()
        self.update_device_selector()
        self.update_top_text_selector()
        self.update_middle_text_selector()
        self.update_bottom_text_selector()

        return rows

    def set_settings_defaults(self):
        """
        Set the default settings for the action
        """

        # Set defaults for device selection
        if "device_name_" + self.actionName not in self.internal_settings:
            self.internal_settings["device_name_" + self.actionName] = None
        if "device_id_" + self.actionName not in self.internal_settings:
            self.internal_settings["device_id_" + self.actionName] = None
        if "show_device_label_" + self.actionName not in self.internal_settings:
            self.internal_settings["show_device_label_" + self.actionName] = False

        # Set defaults for top text selection
        if "top_text_" + self.actionName not in self.internal_settings:
            self.internal_settings["top_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

        # Set defaults for middle text selection
        if "middle_text_" + self.actionName not in self.internal_settings:
            self.internal_settings["middle_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

        # Set defaults for bottom text selection
        if "bottom_text_" + self.actionName not in self.internal_settings:
            self.internal_settings["bottom_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

    def update_device_selector(self):
        """
        Update the device selector with the available devices
        """
        log.debug("Updating device selector")

        # Clear the model and add the currently active device
        self.devices_model.append(["Currently Active", None])
        self.avail_devices = self.backend.get_devices()
        for device in self.avail_devices:
            log.debug("Add Device: " + str(device))
            self.devices_model.append([device["name"], device["id"]])


        # Set index of combo box to last selected device
        # If the device is not in the list, set it to 0 and set settings to the first device
        log.debug("Selected device in Settings: " + str(self.internal_settings["device_name_" + self.actionName]))
        if self.internal_settings["device_name_" + self.actionName] is not None:
            self.devices_select.combo_box.set_active(self.get_index_of_id(self.internal_settings["device_id_" + self.actionName]))
        else:
            log.debug("Selected device not in list. Set to 0")
            self.devices_select.combo_box.set_active(0)
            self.internal_settings["device_name_" + self.actionName] = None
            self.internal_settings["device_id_" + self.actionName] = None

    def update_top_text_selector(self):
        """
        Update the top text selector with the available options
        """
        log.debug("Updating top text selector")

        # Clear the model and add the options
        self.Top_Text_model.clear()
        for option in TextOptions:
            self.Top_Text_model.append([self.text_settings[option], option.value])

        # Set index of combo box to last selected option
        log.debug("Selected top text in Settings: " + str(self.internal_settings["top_text_" + self.actionName]))
        if self.internal_settings["top_text_" + self.actionName] is not None:
            position = 0
            for elem in self.Top_Text_model:
                if elem[1] == self.internal_settings["top_text_" + self.actionName]:
                    log.debug("Found top text " + elem[0] + " with value " + elem[1])
                    self.Top_Text_select.combo_box.set_active(position)
                    break
                position += 1
        else:
            log.debug("Selected top text not in list. Set to 0")
            self.Top_Text_select.combo_box.set_active(0)
            self.internal_settings["top_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

    def update_middle_text_selector(self):
        """
        Update the middle text selector with the available options
        """
        log.debug("Updating middle text selector")

        # Clear the model and add the options
        self.Middle_Text_model.clear()
        for option in TextOptions:
            self.Middle_Text_model.append([self.text_settings[option], option.value])

        settings = self.action_base.get_settings()

        # Set index of combo box to last selected option
        log.debug("Selected middle text in Settings: " + str(settings["middle_text_" + self.actionName]))
        if settings["middle_text_" + self.actionName] is not None:
            position = 0
            for elem in self.Middle_Text_model:
                if elem[1] == settings["middle_text_" + self.actionName]:
                    log.debug("Found middle text " + elem[0] + " with value " + elem[1])
                    self.Middle_Text_select.combo_box.set_active(position)
                    break
                position += 1
        else:
            log.debug("Selected middle text not in list. Set to 0")
            self.Middle_Text_select.combo_box.set_active(0)
            self.internal_settings["middle_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

    def update_bottom_text_selector(self):
        """
        Update the bottom text selector with the available options
        """
        log.debug("Updating bottom text selector")

        # Clear the model and add the options
        self.Bottom_Text_model.clear()
        for option in TextOptions:
            self.Bottom_Text_model.append([self.text_settings[option], option.value])

        # Set index of combo box to last selected option
        log.debug("Selected bottom text in Settings: " + str(self.internal_settings["bottom_text_" + self.actionName]))
        if self.internal_settings["bottom_text_" + self.actionName] is not None:
            position = 0
            for elem in self.Bottom_Text_model:
                if elem[1] == self.internal_settings["bottom_text_" + self.actionName]:
                    log.debug("Found bottom text " + elem[0] + " with value " + elem[1])
                    self.Bottom_Text_select.combo_box.set_active(position)
                    break
                position += 1
        else:
            log.debug("Selected bottom text not in list. Set to 0")
            self.Bottom_Text_select.combo_box.set_active(0)
            self.internal_settings["bottom_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

    def on_device_select(self, combo_box, *args):
        """
        Called when the user selects a device from the combo box
        """
        self.internal_settings["device_name"] = self.devices_model[combo_box.get_active()][0]
        self.internal_settings["device_id"] = self.devices_model[combo_box.get_active()][1]
        self.set_settings(self.internal_settings)

        log.debug("Device selected: " + self.devices_model[combo_box.get_active()][0])

    def on_top_text_select(self, combo_box, *args):
        """
        Called when the user selects a top text option from the combo box
        """
        self.internal_settings["top_text_" + self.actionName] = self.Top_Text_model[combo_box.get_active()][1]

        log.debug("Top text selected: " + self.Top_Text_model[combo_box.get_active()][0])

    def on_middle_text_select(self, combo_box, *args):
        """
        Called when the user selects a middle text option from the combo box
        """
        self.internal_settings["middle_text_" + self.actionName] = self.Middle_Text_model[combo_box.get_active()][1]
        self.internal_settings["middle_text_" + self.actionName] = self.Middle_Text_model[combo_box.get_active()][1]
        log.debug("Middle text selected: " + self.Middle_Text_model[combo_box.get_active()][0])

    def on_bottom_text_select(self, combo_box, *args):
        """
        Called when the user selects a bottom text option from the combo box
        """
        self.internal_settings["bottom_text_" + self.actionName] = self.Bottom_Text_model[combo_box.get_active()][1]

        log.debug("Bottom text selected: " + self.Bottom_Text_model[combo_box.get_active()][0])

    def get_device_id_from_name(self, name: str) -> str:
        """
        Get the device id from the device name
        """
        for device in self.avail_devices:
            if device["name"] == name:
                return device["id"]
        return None

    def get_index_of_id(self, device_id: str) -> int:
        """
        Get the index of the device id within the combo box
        """
        position = 0
        if device_id is None:
            log.debug("Device id is None => Device is the current active device")
            return 0

        if len(self.devices_model) == 0:
            log.debug("Device model is empty, returning position 0")
            return 0

        for elem in self.devices_model:
            log.debug("Checking device " + elem[0] + " with id " + device_id)
            if elem[1] == device_id:
                log.debug("Found device " + elem[0] + " with id " + device_id)
                return position
            position += 1
        log.debug("Position of device " + elem[0] + " is " + str(position))
        return position

    def get_text(self, text_type: Texts) -> str:
        self.backend.set_action_active(True)

        if self.internal_settings[text_type.value + "_text_" + self.actionName] == TextOptions.NONE:
            return ""
        if self.internal_settings[text_type.value + "_text_" + self.actionName] == TextOptions.DEVICE_NAME:
            return self.backend.get_active_device_name()
        if self.internal_settings[text_type.value + "_text_" + self.actionName] == TextOptions.TRACK_NAME:
            track = self.backend.get_current_track()
            if track is not None and "name" in track:
                return track["name"]
            else:
                return ""
        if self.internal_settings[text_type.value + "_text_" + self.actionName] == TextOptions.ARTIST_NAME:
            track = self.backend.get_current_track()
            if track is not None and "artists" in track and len(track["artists"]) > 0:
                return track["artists"][0]["name"]
            else:
                return ""
        if self.internal_settings[text_type.value + "_text_" + self.actionName] == TextOptions.ALBUM_NAME:
            track = self.backend.get_current_track()
            if track is not None and "album" in track and "name" in track["album"]:
                return track["album"]["name"]
            else:
                return ""
        if self.internal_settings[text_type.value + "_text_" + self.actionName] == TextOptions.VOLUME:
            volume = self.backend.get_volume()
            if volume is not None:
                return str(volume) + "%"
            else:
                return ""
        return ""
