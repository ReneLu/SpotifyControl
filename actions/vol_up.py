# Import StreamController modules
from GtkHelper.GtkHelper import ComboRow
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

class VolUpAction(ActionBase):

    actionNameStart = "vol_up"
    actionName = actionNameStart
    backend = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True
        self.actionName = self.actionNameStart + "_" + str(self.input_ident.json_identifier) + "_" + self.page.get_name().replace(" ", "_")
        self.actionSettings = ActionSettings(self.actionName, self.backend)
        self.Texts = Texts

        self.has_configuration = True

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
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-incr-vol-100.png")

            btn_img = self.actionSettings.get_media(self.deck_controller.deck.key_image_format()["size"], icon_path=icon_path)
            if btn_img is not None:
                self.set_media(image=btn_img)
            else:
                self.set_media(None)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        settings = self.actionSettings.get_settings()
        selected_device = settings["device_id_" + self.actionName]
        if self.backend.is_authed():
            old_vol = self.backend.get_volume()
            if old_vol is None:
                return
            new_vol = old_vol + settings["vol_chng_" + self.actionName]
            if new_vol >= 100:
                new_vol = 100
            self.backend.set_volume(new_vol, selected_device)

    ### Action Specific Settings Setup ###
    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            rows = self.actionSettings.get_config_rows()

            self.vol_chng = Adw.SpinRow.new_with_range(0, 100, 1)
            self.vol_chng.set_title(self.plugin_base.lm.get("actions.vol-up.vol-spin.label"))
            self.vol_chng.set_subtitle(self.plugin_base.lm.get("actions.vol-up.vol-spin.subtitle"))

            self.vol_chng.connect("notify::value", self.on_volume_change)

            self.set_settings_defaults()

            self.vol_chng.set_value(self.actionSettings.get_settings().get("vol_chng_" + self.actionName, 5))

            rows.append(self.vol_chng)

            return rows

        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]

    def set_settings_defaults(self):
        """
        Set the default settings for the action
        """
        settings = self.actionSettings.get_settings()
        if "vol_chng_" + self.actionName not in settings:
            settings["vol_chng_" + self.actionName] = 5
        self.actionSettings.set_settings(settings)

    def on_volume_change(self, spin, *args):
        settings = self.actionSettings.get_settings()
        settings["vol_chng_" + self.actionName] = spin.get_value()
        self.actionSettings.set_settings(settings)

    def on_page_rename(self, old_name, new_name):
        if old_name == self.page.get_name():
            old_action_name = self.actionName
            self.actionName = self.actionNameStart + "_" + str(self.input_ident.json_identifier) + "_" + new_name.replace(" ", "_")
            self.actionSettings.rename_setting(old_action_name, self.actionName)

    def on_remove(self) -> None:
        self.actionSettings.remove_setting(self.actionName)
