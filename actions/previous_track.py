# Import StreamController modules
from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger as log

class PrevTrackAction(ActionBase):

    backend = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True

    def on_ready(self) -> None:
        self.set_settings_defaults()
        self.on_tick()

    def on_tick(self) -> None:
        if not self.backend.is_authed():
            #log.debug("Spotify is not authenticated")
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
        else:
            self.backend.set_action_active(True)
            settings = self.get_settings()

            if settings["show_device_label"] == True:
                if settings["device_id"] is None:
                    name = self.backend.get_active_device_name()
                else:
                    name = settings["device_name"]
                self.set_bottom_label(str(name))
            else:
                self.set_bottom_label("")

            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-track-back-100.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        log.debug("Toggle Play / Pause mode")
        settings = self.get_settings()
        selected_device = settings["device_id"]
        if self.backend.is_authed():
            log.debug("Playing previous song.")
            self.backend.previous_track(selected_device)

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            # Create Device Selector Element
            self.devices_model = Gtk.ListStore.new([str, str])
            self.devices_select = ComboRow(model=self.devices_model,
                                           title=self.plugin_base.lm.get("actions.base.device-select.label"))

            self.device_selector_renderer = Gtk.CellRendererText()
            self.devices_select.combo_box.pack_start(self.device_selector_renderer, True)
            self.devices_select.combo_box.add_attribute(self.device_selector_renderer, "text", 0)

            self.label_device_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.base.show-name-switch.label"),
                                              subtitle=self.plugin_base.lm.get("actions.base.show-name-switch.subtitle"))

            self.label_track_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.next-track.show-name.label"),
                                              subtitle=self.plugin_base.lm.get("actions.next-track.show-name.subtitle"))

            self.devices_select.combo_box.connect("changed", self.on_device_select)
            self.label_device_toggle.connect("notify::active", self.on_toggle_device_label)
            self.label_track_toggle.connect("notify::active", self.on_toggle_track_label)
            self.set_settings_defaults()

            self.label_device_toggle.set_active(self.get_settings().get("show_device_label", False))
            self.label_track_toggle.set_active(self.get_settings().get("show_track_label", False))

            self.update_device_selector()
            return [self.devices_select, self.label_device_toggle]

        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]

    ### Custom Methods ###
    def set_settings_defaults(self):
        """
        Set the default settings for the action
        """
        settings = self.get_settings()
        if "device_name" not in settings:
            settings["device_name"] = None
        if "device_id" not in settings:
            settings["device_id"] = None
        if "show_device_label" not in settings:
            settings["show_device_label"] = False
        if "show_track_label" not in settings:
            settings["show_track_label"] = False
        self.set_settings(settings)

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

        settings = self.get_settings()

        # Set index of combo box to last selected device
        # If the device is not in the list, set it to 0 and set settings to the first device
        log.debug("Selected device in Settings: " + str(settings["device_name"]))
        if settings["device_name"] is not None:
            self.devices_select.combo_box.set_active(self.get_index_of_id(settings["device_id"]))
        else:
            log.debug("Selected device not in list. Set to 0")
            self.devices_select.combo_box.set_active(0)
            settings["device_name"] = None
            settings["device_id"] = None

        self.set_settings(settings)

    def on_device_select(self, combo_box, *args):
        """
        Called when the user selects a device from the combo box
        """
        settings = self.get_settings()
        settings["device_name"] = self.devices_model[combo_box.get_active()][0]
        settings["device_id"] = self.devices_model[combo_box.get_active()][1]
        self.set_settings(settings)

        log.debug("Device selected: " + self.devices_model[combo_box.get_active()][0])

    def on_toggle_device_label(self, switch, *args):
        settings = self.get_settings()
        settings["show_device_label"] = switch.get_active()
        self.set_settings(settings)

    def on_toggle_track_label(self, switch, *args):
        settings = self.get_settings()
        settings["show_track_label"] = switch.get_active()
        self.set_settings(settings)

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
