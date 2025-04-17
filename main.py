import os

# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.shuffle import ShuffleAction
from settings import PluginSettings

class SpotifyControl(PluginBase):
    def __init__(self):
        super().__init__()

        self.lm = self.locale_manager
        self.lm.set_to_os_default()

        # Get general settings
        self._settings_manager = PluginSettings(self)
        self.has_plugin_settings = True

        ## Launch backend
        backend_path = os.path.join(self.PATH, "backend", "backend.py")
        self.launch_backend(backend_path=backend_path, open_in_terminal=False,
                            venv_path=os.path.join(self.PATH, "backend", '.venv'))

        ## Register actions
        self.shuffle_action_holder = ActionHolder(
            plugin_base = self,
            action_base = ShuffleAction,
            action_id = "dev_ReneLu_SpotifyControl::ShuffleAction",
            action_name = "Shuffle Action",
        )
        self.add_action_holder(self.shuffle_action_holder)

        # Register plugin
        self.register(
            plugin_name = "Spotify Control",
            github_repo = "https://github.com/ReneLu/SpotifyControl",
            plugin_version = "0.0.1-alpha",
            app_version = "1.1.1-alpha"
        )

    def get_settings_area(self):
        return self._settings_manager.get_settings_area()
