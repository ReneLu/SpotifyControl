# Import StreamController modules
from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

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

class PlayPauseAction(ActionBase):

    actionName = "play_pause"
    backend = None

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
            #log.debug("Spotify is not authenticated")
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
        else:
            #log.debug("Spotify is authenticated")
            self.set_top_label(self.actionSettings.get_text(self.Texts.TOP))
            self.set_center_label(self.actionSettings.get_text(self.Texts.MIDDLE))
            self.set_bottom_label(self.actionSettings.get_text(self.Texts.BOTTOM))

            # Set the play/pause icon
            playback_state = self.backend.get_playback_state()
            if playback_state == True:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-pause-100.png")
            else:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-play-100.png")

        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        log.debug("Toggle Play / Pause mode")
        settings = self.actionSettings.get_settings()
        selected_device = settings["device_id"]
        if self.backend.is_authed():
            if self.backend.get_playback_state() == True:
                log.debug("Playing a song. Pause it.")
                self.backend.pause(selected_device)
            else:
                log.debug("Song paused. Start playing it.")
                self.backend.play(selected_device)

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            return self.actionSettings.get_config_rows()
        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]
