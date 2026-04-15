from streamcontroller_plugin_tools import BackendBase

import os
import spotipy
import webbrowser
from loguru import logger as log
import flask_auth as flaskApp
import threading, time
import requests

CACHE_PATH = os.path.join(os.path.dirname(__file__), ".cache")
KEY_CLIENT_ID = "client_id"
KEY_PORT_REDIRECT_URI = "port_redirect_uri"
ALBUMCOVER_PATH = os.path.join(os.path.dirname(__file__), "cache", "album_covers")

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
    port: int = 0
    redirect_uri = None

    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control"

    def __init__(self):
        super().__init__()

        # Load stored credentials
        self.client_id = self.get_setting(KEY_CLIENT_ID, "")
        raw_port = self.get_setting(KEY_PORT_REDIRECT_URI, 8080)
        try:
            self.port = int(float(raw_port))
        except (TypeError, ValueError):
            self.port = 8080


        self.cache_handler = spotipy.cache_handler.CacheFileHandler(CACHE_PATH)
        if os.path.isfile(CACHE_PATH) and self.client_id and self.port:
            self.redirect_uri = "http://127.0.0.1:" + str(self.port)
            self.auth_manager = spotipy.oauth2.SpotifyPKCE(scope=self.scope,
                                                    redirect_uri = self.redirect_uri,
                                                    client_id = self.client_id,
                                                    cache_handler=self.cache_handler,
                                                    open_browser=True)
            if self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
                self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)

        if not self.reauthenticate(str(self.client_id), self.port):
            log.error("Failed to authenticate with cached credentials")

        os.makedirs(ALBUMCOVER_PATH, exist_ok=True)

        self.ticked_api_call_thread = threading.Thread(target=self.ticked_api_call)
        self.ticked_api_call_thread.daemon = True
        self.ticked_api_call_thread.start()

    ### Setters and Getters ###
    def get_setting(self, key: str, default = None):
        return self.frontend.get_settings().get(key, default)

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
            flaskApp.start_server(self, self.port)
            webbrowser.open_new_tab(self.auth_manager.get_authorize_url())

        self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)

    def complete_authentication(self, token) -> bool:
        """
        Call this after the user has authenticated in the browser.
        """
        if token:
            self.auth_manager.get_access_token(token)
            self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)
            return True
        return False

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
            return False

        self.cache_handler = spotipy.cache_handler.CacheFileHandler(CACHE_PATH)
        self.auth_manager = spotipy.oauth2.SpotifyPKCE(scope=self.scope,
                                                redirect_uri = self.redirect_uri,
                                                client_id = self.client_id,
                                                cache_handler=self.cache_handler,
                                                open_browser=True)

        if not self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
            return False

        try:
            self.auth_manager.get_access_token(CACHE_PATH)
            self.spotifyObject = spotipy.Spotify(auth_manager=self.auth_manager)
        except (spotipy.exceptions.SpotifyException, spotipy.oauth2.SpotifyOauthError) as e:
            log.error("Failed to create Spotify object: " + str(e))
            return False

        return True

    ### WebAPI Access functions ###
    def ticked_api_call(self):
        """
        Call the Spotify API every 1 second
        """
        self.ticked_api_call_thread_started = True
        while True:

            while time.time() - self.last_active_api_call > 5:
                # Wait for action on ticked API call
                self.current_playback_response = None
                time.sleep(1)

            if self.is_authed():
                try:
                    self.current_playback_response = self.spotifyObject.current_playback()
                    self.deviceList= self.spotifyObject.devices()
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
        self.last_active_api_call = time.time()

    ### Player Control ###
    def get_devices(self):
        """
        Get the list of devices
        """
        if not self.is_authed():
            return None

        if self.deviceList is None:
            return None

        if 'devices' in self.deviceList:
            return self.deviceList['devices']
        else:
            return None

    def get_active_device_id(self):
        """
        Get the active device ID
        """
        if self.deviceList is None:
            return None

        for device in self.deviceList['devices']:
            if device['is_active']:
                return device['id']
        return None

    def get_active_device_name(self):
        """
        Get the active device ID
        """
        if self.deviceList is None:
            return None

        for device in self.deviceList['devices']:
            if device['is_active']:
                return device['name']
        return None

    def is_authed(self) -> bool:
        """
        Check if the user is authenticated
        """
        if os.path.isfile(CACHE_PATH):
            if self.auth_manager:
                if self.auth_manager.validate_token(self.auth_manager.get_cached_token()):
                    if flaskApp.get_server_status():
                        flaskApp.stop_server()
                    return True
        return False

    def get_shuffle_mode(self) -> bool:
        """
        Get the current shuffle mode
        """
        if not self.get_active_device_id():
            return False

        curPlayback = self.current_playback_response
        if curPlayback is None:
            return False
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
        self.spotifyObject.pause_playback(device_id=device_id)

    def play(self, device_id) -> None:
        """
        Play the playback
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        self.spotifyObject.start_playback(device_id=device_id)

    def next_track(self, device_id) -> None:
        """
        Play the next track
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        self.spotifyObject.next_track(device_id=device_id)

    def previous_track(self, device_id) -> None:
        """
        Play the previous track
        """
        if device_id is None:
            device_id = self.get_active_device_id()

        if device_id is None:   # No active Device found
            return
        self.spotifyObject.previous_track(device_id=device_id)

    def set_volume(self, volume: int, device_id) -> None:
        """
        Set the volume
        """
        if device_id is None:
            device_id = self.get_active_device_id()
        self.spotifyObject.volume(int(volume), device_id=device_id)

    def get_volume(self) -> int:
        """
        Get the current volume
        """
        curPlayback = self.current_playback_response
        if curPlayback is None:
            return None
        if curPlayback['device']['supports_volume']:
            return curPlayback['device']['volume_percent']
        else:
            return None

    def get_duration_ms(self) -> int:
        """
        Get the duration of the current track in milliseconds
        """
        curPlayback = self.current_playback_response
        if curPlayback is None:
            return None
        if 'item' in curPlayback and curPlayback['item'] is not None:
            return curPlayback['item']['duration_ms']
        else:
            return None

    def get_elapsed_ms(self) -> int:
        """
        Get the elapsed time of the current track in milliseconds
        """
        curPlayback = self.current_playback_response
        if curPlayback is None:
            return None
        return curPlayback['progress_ms']

    def get_remaining_ms(self) -> int:
        """
        Get the remaining time of the current track in milliseconds
        """
        duration = self.get_duration_ms()
        elapsed = self.get_elapsed_ms()
        if duration is not None and elapsed is not None:
            return max(0, duration - elapsed)
        else:
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

        self.spotifyObject.repeat(repeat, device_id)

    def get_current_repeat_state(self) -> str:
        """
        Get the current shuffle mode
        """
        if not self.get_active_device_id():
            return None

        curPlayback = self.current_playback_response
        if curPlayback is None:
            return None

        return curPlayback['repeat_state'] # context - Repeat playlist, track - Repeat track, off - Repeat off

    def get_current_track_info(self) -> dict:
        """
        Get the current track info
        """
        curPlayback = self.current_playback_response
        if curPlayback is None:
            return None

        if 'item' in curPlayback and curPlayback['item'] is not None:
            track_info = {
                'name': curPlayback['item']['name'],
                'artists': [artist['name'] for artist in curPlayback['item']['artists']],
                'album': curPlayback['item']['album']['name'],
                'duration_ms': curPlayback['item']['duration_ms'],
                'progress_ms': curPlayback['progress_ms']
            }
            return track_info
        else:
            return None

    def get_album_cover_path(self) -> str:
        """
        Get the album cover of the current track as a path in cache
        """
        info = self.get_album_cover_info()
        if info and "url" in info and "id" in info:
            album_cover_path = os.path.join(ALBUMCOVER_PATH, info["id"] + ".png")
            # Use cached album cover if it exists
            if os.path.exists(album_cover_path):
                return album_cover_path

            # Delete old album covers if there are more than 5 in the cache
            album_covers = sorted(os.listdir(ALBUMCOVER_PATH), key=lambda x: os.path.getmtime(os.path.join(ALBUMCOVER_PATH, x)))
            if len(album_covers) > 5:
                for album_cover in album_covers[:-5]:
                    try:
                        os.remove(os.path.join(ALBUMCOVER_PATH, album_cover))
                    except Exception as e:
                        log.error("Failed to delete old album cover: " + str(e))

            # Download and save the album cover from URL
            if not self.save_image_from_url(info["url"], album_cover_path):
                log.error("Failed to save album cover from URL")
                return ""
            return album_cover_path

        return ""

    def get_album_cover_info(self) -> dict:
        """
        Get the album cover URL of the current track
        """
        curPlayback = self.current_playback_response
        if curPlayback is None:
            return None

        if 'item' in curPlayback and curPlayback['item'] is not None:
            if 'album' in curPlayback['item'] and 'images' in curPlayback['item']['album'] and len(curPlayback['item']['album']['images']) > 0:
                url = curPlayback['item']['album']['images'][0]['url']
                id = curPlayback['item']['album']['id']
                return { "url": str(url), "id": str(id) }
        return None

    def save_image_from_url(self, url: str = "", save_path: str = "") -> bool:
        """
        Get an image from a URL
        """
        if url == "" or not url or save_path == "" or not save_path:
            return False

        try:
            response = requests.get(url)
            response.raise_for_status()
            f = open(save_path,'wb')
            f.write(response.content)
            f.close()
            return True
        except requests.exceptions.RequestException as e:
            log.error("Failed to get image from URL: " + str(e))
            return False


backend = SpotifyControlBackend()
