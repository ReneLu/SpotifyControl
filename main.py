import os

# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from loguru import logger as log

# Import actions
from .actions.shuffle import ShuffleAction
from .actions.play_pause import PlayPauseAction
from .actions.next_track import NextTrackAction
from .actions.previous_track import PrevTrackAction
from .actions.vol_down import VolDwnAction
from .actions.vol_up import VolUpAction
from .actions.vol_mute import VolMuteAction
from .actions.repeat import RepeatAction
from .actions.vol_set import VolSetAction
from .actions.play import PlayAction
from .actions.pause import PauseAction
from .actions.info import InfoAction
from .actions.element_play import ElementPlayAction

from .spotifysettings import PluginSettings

class SpotifyControl(PluginBase):
    def __init__(self):
        super().__init__()

        self.lm = self.locale_manager
        self.lm.set_to_os_default()

        self._settings_manager = PluginSettings(self)

        ## Launch backend
        backend_path = os.path.join(self.PATH, "backend", "backend.py")
        self.launch_backend(backend_path=backend_path, open_in_terminal=False,
                            venv_path=os.path.join(self.PATH, "backend", '.venv'))

        self._settings_manager = PluginSettings(self)

        ## Register actions
        actions = [
            ("shuffle_action_holder", ShuffleAction, "ShuffleAction", "Shuffle"),
            ("playpause_action_holder", PlayPauseAction, "PlayPauseAction", "Play / Pause"),
            ("nexttrack_action_holder", NextTrackAction, "NextTrackAction", "Next Track"),
            ("prevtrack_action_holder", PrevTrackAction, "PrevTrackAction", "Previous Track"),
            ("vol_dwn_action_holder", VolDwnAction, "VolDwnAction", "Volume Down"),
            ("vol_up_action_holder", VolUpAction, "VolUpAction", "Volume Up"),
            ("vol_mute_action_holder", VolMuteAction, "VolMuteAction", "Volume Mute"),
            ("repeat_action_holder", RepeatAction, "RepeatAction", "Repeat"),
            ("vol_set_action_holder", VolSetAction, "VolSetAction", "Volume Set"),
            ("play_action_holder", PlayAction, "PlayAction", "Play"),
            ("pause_action_holder", PauseAction, "PauseAction", "Pause"),
            ("info_action_holder", InfoAction, "InfoAction", "Info"),
            ("element_play_action_holder", ElementPlayAction, "ElementPlayAction", "Element Play"),
        ]

        for attribute, action, action_id_suffix, action_name in actions:
            action_holder = ActionHolder(
                plugin_base=self,
                action_base=action,
                action_id_suffix=action_id_suffix,
                action_name=action_name,
            )
            setattr(self, attribute, action_holder)
            self.add_action_holder(action_holder)

            # Keep pages created before the plugin ID was corrected working.
            self.add_action_holder(ActionHolder(
                plugin_base=self,
                action_base=action,
                action_id=f"dev_ReneLu_SpotifyControl::{action_id_suffix}",
                action_name=action_name,
            ))

        # Register plugin
        self.register(
            plugin_name = "Spotify Control",
            github_repo = "https://github.com/ReneLu/SpotifyControl",
            plugin_version = "0.0.1-alpha",
            app_version = "1.1.1-alpha"
        )

        self.has_plugin_settings = True

    def get_settings_area(self):
        return self._settings_manager.get_settings_area()
