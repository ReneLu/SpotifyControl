from streamcontroller_plugin_tools import BackendBase

import os
import spotipy
import webbrowser
from loguru import logger as log
import flask_auth as flaskApp

CACHE_PATH = os.path.join(os.path.dirname(__file__), ".cache")

class SpotifyControlBackend(BackendBase):

    cache_handler = None
    auth_manager = None
    spotifyObject = None

    # User Credetials
    client_id = None
    port = None
    redirect_uri = None
    username = None

    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

    def __init__(self):
        super().__init__()
        log.info("Initialize SpotifyControlBackend")

    def get_spotify_object(self):
        """
        Get the spotify object
        """
        return self.spotifyObject

    def get_active_device_id(self):
        """
        Get the active device ID
        """
        for item in self.get_devices():
            if item['is_active']:
                deviceID = item['id']
                log.info("Current active device " + str(item['name'] +
                          " with ID " + str(self.deviceID)))
                return deviceID
        return None

    def get_devices(self):
        """
        Get all devices
        """
        deviceList = self.spotifyObject.devices()
        deviceList = deviceList['devices']
        log.info("Devices: " + str(deviceList))

        return deviceList

    def update_client_credentials(self, client_id: str, port: int):
        if None in (client_id, port) or "" in (client_id, port):
            self.frontend.on_auth_callback(
                False, "actions.base.credentials.missing_client_info")
            return
        self.client_id = client_id
        self.port = int(port)
        self.redirect_uri = "http://127.0.0.1:" + str(self.port)
        self.setup_client()

    def setup_client(self):
        """
        Setup the client
        """
        self.cache_handler = spotipy.cache_handler.CacheFileHandler(CACHE_PATH)
        self.auth_manager = spotipy.oauth2.SpotifyPKCE(scope=self.scope,
                                                redirect_uri = self.redirect_uri,
                                                client_id = self.client_id,
                                                cache_handler=self.cache_handler,
                                                open_browser=True)

        if os.path.isfile(CACHE_PATH) and self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
            self.auth_manager.get_access_token(CACHE_PATH)
        else:
            # Remove not valid token
            if os.path.isfile(CACHE_PATH):
                os.remove(CACHE_PATH)
            flaskApp.start_server(self.port)
            webbrowser.open_new_tab(self.auth_manager.get_authorize_url())
            # Wait for Token set from Flask Server
            while not flaskApp.server.get_token():
                pass
            self.auth_manager.get_access_token(flaskApp.server.get_token())

            flaskApp.stop_server()

        self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)

    def is_authed(self) -> bool:
        """
        Check if the user is authenticated
        """
        return os.path.isfile(CACHE_PATH) and \
               self.auth_manager.validate_token(self.auth_manager.get_cached_token())

    def get_shuffle_mode(self) -> bool:
        """
        Get the current shuffle mode
        """
        curPlayback = self.spotifyObject.current_playback()
        return curPlayback['shuffle_state']

    def shuffle(self, shuffle: bool) -> None:
        """
        Set the shuffle mode
        """
        self.spotifyObject.shuffle(shuffle)

backend = SpotifyControlBackend()
log.info("SpotifyControlBackend initialized")
