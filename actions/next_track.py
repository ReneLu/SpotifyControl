# Import StreamController modules
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

class NextTrackAction(ActionBase):

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
            self.set_center_label("")
            if settings["show_track_label"] == True:
                self.set_bottom_label("Next Track")
            else:
                self.set_bottom_label("")

            if settings["show_device_label"] == True:
                if settings["device_name"] == None:
                    name = self.backend.get_active_device_name()
                else:
                    name = settings["device_name"]
                self.set_bottom_label(str(name))
            else:
                self.set_top_label("")
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-track-forward-100.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        log.debug("Toggle Play / Pause mode")
        settings = self.get_settings()
        selected_device = settings["device_id"]
        if self.backend.is_authed():
            log.debug("Playing next song.")
            self.backend.next_track(selected_device)

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            self.devices_model = Gtk.StringList()
            self.devices_select = Adw.ComboRow(model=self.devices_model,
                                                title=self.plugin_base.lm.get("actions.base.device-select.label"),
                                                subtitle=self.plugin_base.lm.get("actions.base.device-select.subtitle"))
            self.devices_select.set_enable_search(True)
            self.devices_select.connect("notify::selected", self._on_device_select)

            self.label_device_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.base.show-name-switch.label"),
                                              subtitle=self.plugin_base.lm.get("actions.base.show-name-switch.subtitle"))

            self.label_track_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.next-track.show-name.label"),
                                              subtitle=self.plugin_base.lm.get("actions.next-track.show-name.subtitle"))

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
        self.devices_model = Gtk.StringList()
        self.avail_devices = self.backend.get_devices()
        self.devices_model.append("Currently Active")
        for device in self.avail_devices:
            self.devices_model.append(device["name"])
        self.devices_select.set_model(self.devices_model)
        settings = self.get_settings()

        # Set index of combo box to last selected device
        # If the device is not in the list, set it to 0 and set settings to the first device
        log.debug("Selected device in Settings: " + str(settings["device_name"]))
        if settings["device_name"] is not None:
            self.devices_select.set_selected(self.get_index_of_id(self.devices_model, settings["device_name"]) + 1)
        else:
            log.debug("Selected device not in list. Set to 0")
            self.devices_select.set_selected(0)
            settings["device_name"] = None
            settings["device_id"] = None

        self.set_settings(settings)

    def _on_device_select(self, combo, *args):
        """
        Called when the user selects a device from the combo box
        """
        settings = self.get_settings()
        settings["device_name"] = combo.get_selected_item().get_string()
        settings["device_id"] = self.get_device_id_from_name(combo.get_selected_item().get_string())
        self.set_settings(settings)

        log.debug("Selected device: " + settings["device_name"] + " -- " + settings["device_id"])

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

    def get_index_of_id(self, model, name: str) -> int:
        """
        Get the index of the device id within the combo box
        """
        position = 0
        for i in range(model.get_n_items()):
            if model.get_item(i).get_string() == name:
                position = i
                break
        log.debug("Position of device " + name + " is " + str(position))
        return position
