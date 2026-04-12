# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase

# Import action_settings.py from the same folder
from .action_settings import ActionSettings, Texts

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from loguru import logger as log

class VolMuteAction(ActionBase):

    actionName = "vol_mute"
    backend = None
    last_volume = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True
        self.actionSettings = ActionSettings(self.actionName, self.backend)
        self.Texts = Texts

    def on_ready(self) -> None:
        self.actionSettings.set_settings_defaults()
        self.on_tick()

    def on_tick(self) -> None:
        if self.backend is None:
            log.error("Spotify backend is not available")
            return
        if not self.backend.is_authed():
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
        else:
            self.set_top_label(self.actionSettings.get_text(self.Texts.TOP))
            self.set_center_label(self.actionSettings.get_text(self.Texts.MIDDLE))
            self.set_bottom_label(self.actionSettings.get_text(self.Texts.BOTTOM))

            volume = self.backend.get_volume()

            # Set icon
            if volume is None:
                # Set icon to no sound available
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-no-sound-100.png")
            elif volume == 0:
                # Set icon to muted
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-mute-100.png")
            elif volume > 0:
                # Set icon to unmuted
                self.last_volume = volume
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-no-mute-100.png")
            else:
                # Set icon to no sound available
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-no-sound-100.png")

        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle mute
        settings = self.actionSettings.get_settings()
        selected_device = settings["device_id_" + self.actionName]
        if self.backend.is_authed():
            # Get current volume
            current_vol = self.backend.get_volume()
            if current_vol is None:
                return None
            elif current_vol == 0:
                # Set volume to 100
                new_vol = self.last_volume
            elif current_vol > 0:
                # Set volume to 0
                self.last_volume = current_vol
                new_vol = 0
            else:
                return None
            self.backend.set_volume(new_vol, selected_device)

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            return self.actionSettings.get_config_rows()
        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]
