from streamcontroller_plugin_tools import BackendBase

import os
import spotipy
import webbrowser
from loguru import logger as log
import flask_auth as flaskApp
import threading, time

CACHE_PATH = os.path.join(os.path.dirname(__file__), ".cache")

class SpotifyControlBackend(BackendBase):

    cache_handler = None
    auth_manager = None
    spotifyObject = None

    current_playback_response = None
    deviceList = None
    action_active = False
    ticked_api_call_thread = None
    ticked_api_call_thread_started = False
    last_active_api_call = 0.0

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

        self.ticked_api_call_thread = threading.Thread(target=self.ticked_api_call)
        self.ticked_api_call_thread.daemon = True
        self.ticked_api_call_thread.start()
        log.debug("Ticked API call thread started")

    ### Setters and Getters ###
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

    ### Credential Handling ###
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

    ### WebAPI Access functions ###
    def ticked_api_call(self):
        """
        Call the Spotify API every 1 second
        """
        self.ticked_api_call_thread_started = True
        while True:

            log.debug("Ticked API call")
            # self.action_active = False  # Must be set to True from an action to keep thread alive
            while time.time() - self.last_active_api_call > 5:
                # Wait for action on ticked API call
                self.current_playback_response = None

            if self.is_authed():
                try:
                    self.current_playback_response = self.spotifyObject.current_playback()
                    log.debug("Current playback: " + str(self.current_playback_response))
                    self.deviceList= self.spotifyObject.devices()
                    log.debug("Devices: " + str(self.deviceList))
                except spotipy.exceptions.SpotifyException as e:
                    log.error("Error updating spotify data: " + str(e))
                    if e.http_status == 401 or e.http_status == 403:
                        log.error("Spotify token is not valid. Reauthenticating...")
                        self.current_playback_response = None
                        self.deviceList = None
                        self.reauthenticate(self.client_id, self.port)
                    elif e.http_status == 404:
                        log.error("Spotify API not found. Check your client ID and port.")
                        self.current_playback_response = None
                        self.deviceList = None
                    elif e.http_status == 429:
                        log.error("Spotify API rate limit exceeded. Waiting before retrying...")
                        time.sleep(int(e.headers.get('Retry-After', 1)))
                    else:
                        log.error("Spotify API error: " + str(e))
                        self.current_playback_response = None
                        self.deviceList = None
            time.sleep(1)

    def set_action_active(self, active: bool):
        """
        Set the action active
        """
        log.debug("Set action active: " + str(active))
        self.action_active = active
        self.last_active_api_call = time.time()

    ### Player Control ###
    def get_devices(self):
        """
        Get the list of devices
        """
        if not self.is_authed():
            log.debug("Spotify is not authenticated")
            return None

        if self.deviceList is None:
            log.debug("No devices found")
            return None

        if 'devices' in self.deviceList:
            log.debug("Devices found: " + str(len(self.deviceList['devices'])))
            return self.deviceList['devices']
        else:
            log.debug("No devices found")
            return None

    def get_active_device_id(self):
        """
        Get the active device ID
        """
        if self.deviceList is None:
            log.debug("No devices found")
            return None

        for device in self.deviceList['devices']:
            if device['is_active']:
                log.debug("Active Device id: " + str(device['id']))
                return device['id']
        return None

    def get_active_device_name(self):
        """
        Get the active device ID
        """
        if self.deviceList is None:
            log.debug("No devices found")
            return None

        for device in self.deviceList['devices']:
            if device['is_active']:
                log.debug("Active Device name: " + str(device['name']))
                return device['name']
        return None

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

        curPlayback = self.current_playback_response
        if curPlayback is None:
            log.debug("No current playback")
            return None
        return curPlayback['shuffle_state']

    def shuffle(self, shuffle: bool, device_id=None) -> None:
        """
        Set the shuffle mode
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        self.spotifyObject.shuffle(shuffle, device_id=device_id)

    def get_playback_state(self) -> str:
        """
        Get the current playback state
        """
        if not self.get_active_device_id():
            return None

        curPlayback = self.current_playback_response
        if curPlayback is None:
            log.debug("No current playback")
            return None

        return curPlayback['is_playing']

    def pause(self, device_id) -> None:
        """
        Pause the playback
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        log.debug("Pause on device: " + str(device_id))
        self.spotifyObject.pause_playback(device_id=device_id)

    def play(self, device_id) -> None:
        """
        Play the playback
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        log.debug("Play on device: " + str(device_id))
        self.spotifyObject.start_playback(device_id=device_id)

    def next_track(self, device_id) -> None:
        """
        Play the next track
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        log.debug("Next track on device: " + str(device_id))
        self.spotifyObject.next_track(device_id=device_id)

    def previous_track(self, device_id) -> None:
        """
        Play the previous track
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        log.debug("Previous track on device: " + str(device_id))
        self.spotifyObject.previous_track(device_id=device_id)

    def set_volume(self, volume: int, device_id) -> None:
        """
        Set the volume
        """
        if device_id is None:
            device_id = self.get_active_device_id()
        log.debug("Set volume on device: " + str(device_id) + " to " + str(volume))
        self.spotifyObject.volume(int(volume), device_id=device_id)

    def get_volume(self, device_id) -> int:
        """
        Get the current volume
        """
        curPlayback = self.current_playback_response
        if curPlayback is None:
            log.debug("No current playback")
            return None
        if curPlayback['device']['supports_volume']:
            return curPlayback['device']['volume_percent']
        else:
            log.debug("Device " + str(curPlayback['name']) +
                    " does not support volume control")
            return None

    def repeat(self, repeat: str, device_id) -> None:
        """
        Set the repeat mode
        """
        if repeat not in ['off', 'track', 'context']:
            log.error("Invalid repeat mode: " + str(repeat))
            return

        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return

        log.debug("Set repeat on device: " + str(device_id) + " to " + str(repeat))
        self.spotifyObject.repeat(repeat, device_id)

    def get_current_repeat_state(self) -> str:
        """
        Get the current shuffle mode
        """
        if not self.get_active_device_id():
            return None

        curPlayback = self.current_playback_response
        if curPlayback is None:
            log.debug("No current playback")
            return None

        return curPlayback['repeat_state'] # context - Repeat playlist, track - Repeat track, off - Repeat off

backend = SpotifyControlBackend()
log.debug("SpotifyControlBackend initialized")
