# -*- coding: utf-8 -*-
"""Shared foundation: addon handle, paths, strings, logging and audit.

Imported by every other module. It only depends on the Kodi API, so it is safe to load from
any entry point (default.py, context_add.py) without side effects.
"""
import datetime
import os
import sys

import xbmc
import xbmcaddon
import xbmcvfs

translatePath = xbmcvfs.translatePath if hasattr(xbmcvfs, 'translatePath') else xbmc.translatePath

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')

# Plugin invocation identifiers. sys.argv is absent when this module is loaded from a context
# menu script, so it is parsed defensively.
PLUGIN_ID = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].lstrip('-').isdigit() else -1
BASE_URL = sys.argv[0] if sys.argv else ''
if BASE_URL and not BASE_URL.endswith('/'):
    BASE_URL += '/'

PATHS = {
    'favourites': translatePath('special://userdata/favourites.xml'),
    'backup': translatePath('special://userdata/favourites.xml.bak'),
    'addon_path': ADDON.getAddonInfo('path'),
    'templates': os.path.join(ADDON.getAddonInfo('path'), 'resources', 'templates.json'),
    'media': os.path.join(ADDON.getAddonInfo('path'), 'resources', 'media'),
    # Profiles live under addon_data; they persist across updates and stay out of the ZIP.
    'profiles': translatePath(f'special://profile/addon_data/{ADDON_ID}/profiles'),
}
os.makedirs(PATHS['profiles'], exist_ok=True)

# Window properties shared between the skin XML and the editor logic.
PROPS = {
    'result': 'flow_xml_output',
    'reorder_method': 'flow_action_mode',
    'font_size': 'flow_ui_font',
    'thumb_size': 'flow_ui_thumb',
}

AUDIT_FILE = translatePath(f'special://profile/addon_data/{ADDON_ID}/audit.log')


def get_string(string_id):
    text = ADDON.getLocalizedString(string_id)
    if not text:
        xbmc.log(f'[Flow FavManager] Missing string {string_id}', xbmc.LOGWARNING)
        return str(string_id)
    return text


def log_debug(msg):
    xbmc.log(f'[Flow FavManager] {msg}', xbmc.LOGINFO)


def log_audit(action, details):
    """Records security events and notable actions, only when the audit log is enabled."""
    if ADDON.getSetting('enable_audit_log') != 'true':
        return
    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(AUDIT_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{timestamp}] {action}: {details}\n')
    except OSError as e:
        log_debug(f'Could not write audit log: {e}')


class CloseAddon(BaseException):
    """Raised from any menu to close the addon immediately."""
