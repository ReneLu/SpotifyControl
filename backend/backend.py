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

    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control"

    def __init__(self):
        super().__init__()
        log.debug("Initialize SpotifyControlBackend")
        log.debug("Client ID: " + str(self.client_id))
        log.debug("Port: " + str(self.port))

        self.cache_handler = spotipy.cache_handler.CacheFileHandler(CACHE_PATH)
        if os.path.isfile(CACHE_PATH) and self.client_id and self.port:
            self.redirect_uri = "http://127.0.0.1:" + str(self.port)
            log.debug("Cache file found")
            self.auth_manager = spotipy.oauth2.SpotifyPKCE(scope=self.scope,
                                                    redirect_uri = self.redirect_uri,
                                                    client_id = self.client_id,
                                                    cache_handler=self.cache_handler,
                                                    open_browser=True)
            if self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
                self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)

    def set_client_id(self, client_id: str):
        """
        Set the client ID
        """
        self.client_id = client_id

    def set_port(self, port: int):
        """
        Set the port
        """
        self.port = int(port)

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
                log.debug("Current active device " + str(item['name'] +
                          " with ID " + str(deviceID)))
                return deviceID
        return None

    def get_devices(self):
        """
        Get all devices
        """
        deviceList = self.spotifyObject.devices()
        deviceList = deviceList['devices']
        log.debug("Devices: " + str(deviceList))

        return deviceList

    def update_client_credentials(self, client_id: str, port: int):
        """
        Update the client credentials
        """
        if None in (client_id, port) or "" in (client_id, port):
            return False

        self.client_id = client_id
        self.port = int(port)
        self.redirect_uri = "http://127.0.0.1:" + str(self.port)

        self.setup_client()

        return True

    def setup_client(self):
        """
        Setup the client
        """
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

    def reauthenticate(self, client_id: str, port: int):
        """
        Reauthenticate the user
        """
        if None in (client_id, port) or "" in (client_id, port):
            return False

        self.client_id = client_id
        self.port = int(port)
        self.redirect_uri = "http://127.0.0.1:" + str(self.port)

        if not os.path.isfile(CACHE_PATH):
            log.debug("Cache file not found")
            return False

        self.cache_handler = spotipy.cache_handler.CacheFileHandler(CACHE_PATH)
        self.auth_manager = spotipy.oauth2.SpotifyPKCE(scope=self.scope,
                                                redirect_uri = self.redirect_uri,
                                                client_id = self.client_id,
                                                cache_handler=self.cache_handler,
                                                open_browser=True)

        if not self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
            log.debug("Token is not valid")
            return False

        self.auth_manager.get_access_token(CACHE_PATH)
        self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)

        return True

    def is_authed(self) -> bool:
        """
        Check if the user is authenticated
        """
        if os.path.isfile(CACHE_PATH):
            log.debug("Cache file found")
            if self.auth_manager:
                if self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
                    log.debug("Token is valid")
                    return True
        return False

    def get_shuffle_mode(self) -> bool:
        """
        Get the current shuffle mode
        """
        if not self.get_active_device_id():
            return None

        try:
            curPlayback = self.spotifyObject.current_playback()
            log.debug("Current playback: " + str(curPlayback))
            if curPlayback is None:
                log.debug("No current playback")
                return None
        except spotipy.exceptions.SpotifyException as e:
            log.error("Error getting current playback: " + str(e))
            return None

        return curPlayback['shuffle_state']

    def shuffle(self, shuffle: bool) -> None:
        """
        Set the shuffle mode
        """
        self.spotifyObject.shuffle(shuffle)

    def get_playback_state(self) -> str:
        """
        Get the current playback state
        """
        if not self.get_active_device_id():
            return None

        try:
            curPlayback = self.spotifyObject.currently_playing()
            log.debug("Current playback: " + str(curPlayback))
            if curPlayback is None:
                log.debug("No current playback")
                return None
        except spotipy.exceptions.SpotifyException as e:
            log.error("Error getting current playback: " + str(e))
            return None

        return curPlayback['is_playing']

    def pause(self, device_id) -> None:
        """
        Pause the playback
        """
        if device_id is None:
            device_id = self.get_active_device_id()
        log.debug("Pause on device: " + str(device_id))
        self.spotifyObject.pause_playback(device_id=device_id)

    def play(self, device_id) -> None:
        """
        Play the playback
        """
        if device_id is None:
            device_id = self.get_active_device_id()
        log.debug("Play on device: " + str(device_id))
        self.spotifyObject.start_playback(device_id=device_id)

backend = SpotifyControlBackend()
log.debug("SpotifyControlBackend initialized")
