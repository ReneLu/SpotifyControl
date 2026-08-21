import json
import os
from streamcontroller_plugin_tools.installation_helpers import create_venv
from os.path import join, abspath, dirname

LEGACY_ACTION_PREFIX = "dev_ReneLu_SpotifyControl::"
ACTION_PREFIX = "com_ReneLu_spotifyControl::"


def migrate_action_ids():
    pages_path = join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "pages")
    if not os.path.isdir(pages_path):
        return

    for directory, _, file_names in os.walk(pages_path):
        for file_name in file_names:
            if not file_name.endswith(".json"):
                continue

            migrate_page(join(directory, file_name))


def migrate_page(page_path):
    try:
        with open(page_path, "r", encoding="utf-8") as page_file:
            page = json.load(page_file)
    except (OSError, json.JSONDecodeError):
        return

    changed = False
    for input_type in ("keys", "dials", "touchscreens"):
        for input_config in page.get(input_type, {}).values():
            for state in input_config.get("states", {}).values():
                for action in state.get("actions", []):
                    action_id = action.get("id") if isinstance(action, dict) else None
                    if isinstance(action_id, str) and action_id.startswith(LEGACY_ACTION_PREFIX):
                        action["id"] = ACTION_PREFIX + action_id.removeprefix(LEGACY_ACTION_PREFIX)
                        changed = True

    if changed:
        temporary_path = f"{page_path}.spotify-control.tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as page_file:
                json.dump(page, page_file, indent=4)
            os.replace(temporary_path, page_path)
        except OSError:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)


toplevel = dirname(abspath(__file__))
migrate_action_ids()
create_venv(join(toplevel, "backend", ".venv"), join(toplevel, "backend", "requirements.txt"))
