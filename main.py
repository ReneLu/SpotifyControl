import os

# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.shuffle import ShuffleAction
from .actions.play_pause import PlayPauseAction
from .actions.next_track import NextTrackAction
from .actions.previous_track import PrevTrackAction
from .actions.vol_down import VolDwnAction
from .actions.vol_up import VolUpAction
from .actions.vol_mute import VolMuteAction
from .actions.repeat import RepeatAction

from .settings import PluginSettings

class SpotifyControl(PluginBase):
    def __init__(self):
        super().__init__()

        self.lm = self.locale_manager
        self.lm.set_to_os_default()

        ## Launch backend
        backend_path = os.path.join(self.PATH, "backend", "backend.py")
        self.launch_backend(backend_path=backend_path, open_in_terminal=False,
                            venv_path=os.path.join(self.PATH, "backend", '.venv'))

        # Get general settings
        self._settings_manager = PluginSettings(self)
        self.has_plugin_settings = True

        ## Register actions
        self.shuffle_action_holder = ActionHolder(
            plugin_base = self,
            action_base = ShuffleAction,
            action_id = "dev_ReneLu_SpotifyControl::ShuffleAction",
            action_name = "Shuffle",
        )
        self.add_action_holder(self.shuffle_action_holder)

        self.playpause_action_holder = ActionHolder(
            plugin_base = self,
            action_base = PlayPauseAction,
            action_id = "dev_ReneLu_SpotifyControl::PlayPauseAction",
            action_name = "Play / Pause",
        )
        self.add_action_holder(self.playpause_action_holder)

        self.nexttrack_action_holder = ActionHolder(
            plugin_base = self,
            action_base = NextTrackAction,
            action_id = "dev_ReneLu_SpotifyControl::NextTrackAction",
            action_name = "Next Track",
        )
        self.add_action_holder(self.nexttrack_action_holder)

        self.prevtrack_action_holder = ActionHolder(
            plugin_base = self,
            action_base = PrevTrackAction,
            action_id = "dev_ReneLu_SpotifyControl::PrevTrackAction",
            action_name = "Previous Track",
        )
        self.add_action_holder(self.prevtrack_action_holder)

        self.vol_dwn_action_holder = ActionHolder(
            plugin_base = self,
            action_base = VolDwnAction,
            action_id = "dev_ReneLu_SpotifyControl::VolDwnAction",
            action_name = "Volume Down",
        )
        self.add_action_holder(self.vol_dwn_action_holder)

        self.vol_up_action_holder = ActionHolder(
            plugin_base = self,
            action_base = VolUpAction,
            action_id = "dev_ReneLu_SpotifyControl::VolUpAction",
            action_name = "Volume Up",
        )
        self.add_action_holder(self.vol_up_action_holder)

        self.vol_mute_action_holder = ActionHolder(
            plugin_base = self,
            action_base = VolMuteAction,
            action_id = "dev_ReneLu_SpotifyControl::VolMuteAction",
            action_name = "Volume Mute",
        )
        self.add_action_holder(self.vol_mute_action_holder)

        self.repeat_action_holder = ActionHolder(
            plugin_base = self,
            action_base = RepeatAction,
            action_id = "dev_ReneLu_SpotifyControl::RepeatAction",
            action_name = "Repeat",
        )
        self.add_action_holder(self.repeat_action_holder)

        # Register plugin
        self.register(
            plugin_name = "Spotify Control",
            github_repo = "https://github.com/ReneLu/SpotifyControl",
            plugin_version = "0.0.1-alpha",
            app_version = "1.1.1-alpha"
        )

    def get_settings_area(self):
        return self._settings_manager.get_settings_area()
