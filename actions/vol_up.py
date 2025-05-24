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

class VolUpAction(ActionBase):

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

            selected_device = settings["device_id"]
            if self.backend.get_volume(selected_device) is None:
                # Set icon to no sound available
                log.debug("Volume is not available")
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-no-sound-100.png")
            else:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-incr-vol-100.png")

            if settings["show_vol_label"] == True:
                self.set_center_label(str(self.backend.get_volume(settings["device_id"])))
            else:
                self.set_center_label("")

            if settings["show_device_label"] == True:
                if settings["device_id"] == None:
                    name = self.backend.get_active_device_name()
                else:
                    name = settings["device_name"]
                self.set_bottom_label(str(name))
            else:
                self.set_bottom_label("")

        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        settings = self.get_settings()
        selected_device = settings["device_id"]
        if self.backend.is_authed():
            log.debug("Increase volume by " + str(settings["vol_chng"]))
            old_vol = self.backend.get_volume(selected_device)
            if old_vol is None:
                log.debug("Volume is not available")
                return
            new_vol = old_vol + settings["vol_chng"]
            if new_vol >= 100:
                new_vol = 100
            self.backend.set_volume(new_vol, selected_device)

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

            self.label_vol_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.vol-dwn.vol-show.label"),
                                              subtitle=self.plugin_base.lm.get("actions.vol-dwn.vol-show.subtitle"))

            self.vol_chng = Adw.SpinRow.new_with_range(0, 100, 1)
            self.vol_chng.set_title(self.plugin_base.lm.get("actions.vol-up.vol-spin.label"))
            self.vol_chng.set_subtitle(self.plugin_base.lm.get("actions.vol-up.vol-spin.subtitle"))

            self.devices_select.combo_box.connect("changed", self.on_device_select)
            self.label_device_toggle.connect("notify::active", self.on_toggle_device_label)
            self.label_vol_toggle.connect("notify::active", self.on_toggle_track_label)
            self.vol_chng.connect("notify::value", self.on_toggle_volume_change)

            self.set_settings_defaults()

            self.label_device_toggle.set_active(self.get_settings().get("show_device_label", False))
            self.label_vol_toggle.set_active(self.get_settings().get("show_vol_label", False))
            self.vol_chng.set_value(self.get_settings().get("vol_chng", 5))
            self.update_device_selector()

            return [self.devices_select, self.label_device_toggle, self.label_vol_toggle, self.vol_chng]

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
        if "show_vol_label" not in settings:
            settings["show_vol_label"] = False
        if "vol_chng" not in settings:
            settings["vol_chng"] = 5
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
            self.devices_select.combo_box.set_active(self.get_index_of_id(settings["device_name"]))
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
        settings["show_vol_label"] = switch.get_active()
        self.set_settings(settings)

    def on_toggle_volume_change(self, spin, *args):
        settings = self.get_settings()
        settings["vol_chng"] = spin.get_value()
        self.set_settings(settings)
        log.debug("Volume change set to " + str(settings["vol_chng"]))

    def get_device_id_from_name(self, name: str) -> str:
        """
        Get the device id from the device name
        """
        for device in self.avail_devices:
            if device["name"] == name:
                return device["id"]
        return None

    def get_index_of_id(self, name: str) -> int:
        """
        Get the index of the device id within the combo box
        """
        position = 0
        for elem in self.devices_model:
            log.debug("Checking device " + elem[0] + " with id " + str(elem[1]))
            if elem[0] == name:
                log.debug("Found device " + name + " with id " + str(elem[1]))
                break
            position += 1
        log.debug("Position of device " + name + " is " + str(position))
        return position
