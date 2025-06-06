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

class RepeatAction(ActionBase):

    backend = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend

    def on_ready(self) -> None:
        self.set_settings_defaults()

    def on_tick(self) -> None:
        if not self.backend.is_authed():
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
        else:
            settings = self.get_settings()
            if settings["show_device_label"] == True:
                self.set_top_label(str(settings["device_name"]))
            else:
                self.set_top_label("")

            repeat_state = self.backend.get_current_repeat_state()
            if repeat_state == "off":
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-off-100.png")
                self.set_top_label("")
                self.set_center_label("")
                self.set_bottom_label("")
            elif repeat_state == "context":
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-100.png")
                self.set_top_label("")
                self.set_center_label("")
                self.set_bottom_label("")
            elif repeat_state == "track":
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-1-100.png")
                self.set_top_label("")
                self.set_center_label("")
                self.set_bottom_label("")
            else:
                log.debug("Repeat mode is None")
                self.set_top_label("")
                self.set_center_label("")
                self.set_bottom_label("")
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-no-music-100.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        log.debug("Toggle Repeat mode")
        if self.backend.is_authed():
            repeat_state = self.backend.get_current_repeat_state()
            settings = self.get_settings()
            selected_device = settings["device_id"]
            if repeat_state == "off":
                log.debug("Repeat mode is Off")
                self.backend.repeat("context", selected_device)
            elif repeat_state == "context":
                log.debug("Repeat mode is Context")
                self.backend.repeat("track", selected_device)
            elif repeat_state == "track":
                log.debug("Repeat mode is Track")
                self.backend.repeat("off", selected_device)
            else:
                log.debug("Repeat mode is None")
                self.set_top_label("Repeat")
                self.set_center_label("No Music")
                self.set_bottom_label("Playing")

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

            self.label_device_toggle.connect("notify::active", self.on_toggle_device_label)

            self.set_settings_defaults()

            self.label_device_toggle.set_active(self.get_settings().get("show_device_label", False))
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
        self.set_settings(settings)

    def update_device_selector(self):
        """
        Update the device selector with the available devices
        """
        log.debug("Updating device selector")
        self.devices_model = Gtk.StringList()
        self.avail_devices = self.backend.get_devices()
        for device in self.avail_devices:
            self.devices_model.append(device["name"])
        self.devices_select.set_model(self.devices_model)
        settings = self.get_settings()

        # Set index of combo box to last selected device
        # If the device is not in the list, set it to 0 and set settings to the first device
        log.debug("Selected device in Settings: " + str(settings["device_name"]))
        if settings["device_name"] is not None:
            self.devices_select.set_selected(self.get_index_of_id(self.devices_model, settings["device_name"]))
        else:
            log.debug("Selected device not in list. Set to 0")
            self.devices_select.set_selected(0)
            if len(self.avail_devices) > 0:
                settings["device_name"] = self.avail_devices[0]["name"]
                settings["device_id"] = self.avail_devices[0]["id"]
            else:
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
        settings["show_vol_label"] = switch.get_active()
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
