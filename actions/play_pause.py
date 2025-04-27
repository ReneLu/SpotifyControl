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

class PlayPauseAction(ActionBase):

    backend = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend

    def on_ready(self) -> None:
        self.set_settings_defaults()

    def on_tick(self) -> None:
        if not self.backend.is_authed():
            #log.debug("Spotify is not authenticated")
            self.set_media(media_path="")
            self.set_top_label("Spotify")
            self.set_center_label("Not")
            self.set_bottom_label("Authed")
        else:
            #log.debug("Spotify is authenticated")
            playback_state = self.backend.get_playback_state()
            log.debug("Playback state: " + str(playback_state))
            settings = self.get_settings()

            if playback_state == True:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-pause-100.png")
            else:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-play-100.png")

            self.set_top_label("")
            self.set_center_label("")
            if settings["show_label"] == True:
                self.set_bottom_label(str(settings["device_name"]))
            else:
                self.set_bottom_label("")
            self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        log.debug("Toggle Play / Pause mode")
        settings = self.get_settings()
        selected_device = settings["device_id"]
        if self.backend.is_authed() and selected_device is not None:
            if self.backend.get_playback_state() == True:
                log.debug("Playing a song. Pause it.")
                self.backend.pause(selected_device)
            else:
                log.debug("Song paused. Start playing it.")
                self.backend.play(selected_device)

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            self.devices_model = Gtk.StringList()
            self.devices_select = Adw.ComboRow(model=self.devices_model,
                                                title=self.plugin_base.lm.get("actions.playpause.device-select.label"),
                                                subtitle=self.plugin_base.lm.get("actions.playpause.device-select.subtitle"))
            self.devices_select.set_enable_search(True)
            self.devices_select.connect("notify::selected", self._on_device_select)

            self.label_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.playpause.show-name-switch.label"),
                                              subtitle=self.plugin_base.lm.get("actions.playpause.show-name-switch.subtitle"))

            self.label_toggle.connect("notify::active", self.on_toggle_label)
            self.set_settings_defaults()

            self.label_toggle.set_active(self.get_settings().get("show_label", False))

            self.update_device_selector()
            return [self.devices_select, self.label_toggle]

        else:
            self.not_authed_label = Adw.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
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
        if "show_label" not in settings:
            settings["show_label"] = False
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

    def on_toggle_label(self, switch, *args):
        settings = self.get_settings()
        settings["show_label"] = switch.get_active()
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
