# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase

# Import action_settings.py from the same folder
from .action_settings import ActionSettings, Texts

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger as log

class VolSetAction(ActionBase):

    actionName = "vol_set"
    backend = None
    last_volume = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True
        self.actionName = self.actionName + "_" + str(self.input_ident.json_identifier) + "_" + self.page.get_name().replace(" ", "_")
        self.actionSettings = ActionSettings(self.actionName, self.backend)
        self.Texts = Texts

    def on_ready(self) -> None:
        self.actionSettings.set_settings_defaults()
        self.on_tick()

    def on_tick(self) -> None:
        if not self.backend.is_authed():
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
            self.set_media(media_path=icon_path, size=0.75)
        else:
            # Set Labels
            self.set_top_label(self.actionSettings.get_text(self.Texts.TOP))
            self.set_center_label(self.actionSettings.get_text(self.Texts.MIDDLE))
            self.set_bottom_label(self.actionSettings.get_text(self.Texts.BOTTOM))

            icon_path = ""
            volume = self.backend.get_volume()
            if volume is None:
                # Set icon to no sound available
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-no-sound-100.png")
            else:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-sound-100.png")

            btn_img = self.actionSettings.get_media(icon_path=icon_path)
            if btn_img is not None:
                self.set_media(image=btn_img)
            else:
                self.set_media(None)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        settings = self.actionSettings.get_settings()
        selected_device = settings["device_id_" + self.actionName]
        if self.backend.is_authed():
            self.backend.set_volume(int(settings["volume_" + self.actionName]), selected_device)

    ### Action Specific Settings Setup ###
    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            rows = self.actionSettings.get_config_rows()

            self.vol_val = Adw.SpinRow.new_with_range(0, 100, 1)
            self.vol_val.set_title(self.plugin_base.lm.get("actions.vol-set.vol-spin.label"))
            self.vol_val.set_subtitle(self.plugin_base.lm.get("actions.vol-set.vol-spin.subtitle"))
            self.vol_val.connect("changed", self.on_volume_change)

            self.set_settings_defaults()

            self.vol_val.set_value(self.actionSettings.get_settings().get("volume_" + self.actionName, 50))

            rows.append(self.vol_val)

            return rows

        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]

    def set_settings_defaults(self):
        """
        Set the default settings for the action
        """
        settings = self.actionSettings.get_settings()
        if "volume_" + self.actionName not in settings:
            settings["volume_" + self.actionName] = 50
        self.actionSettings.set_settings(settings)

    def on_volume_change(self, spin, *args):
        settings = self.actionSettings.get_settings()
        settings["volume_" + self.actionName] = spin.get_value()
        self.actionSettings.set_settings(settings)