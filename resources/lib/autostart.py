# -*- coding: utf-8 -*-
"""Auto-start configuration menu (3 slots).

Writes the autofav_{1..3}_* settings that service.py reads on Kodi launch. The delay list MUST
match _DELAY_MAP in service.py, which is standalone and does not import this module.
"""
import re

import xbmcgui

from resources.lib.common import ADDON, CloseAddon, get_string, log_audit
from resources.lib.database import FavouritesEngine
from resources.lib.listing import normalize_url

SLOTS = 3
DELAY_VALUES = [0, 5, 10, 15, 30, 60]  # in seconds; must match service.py


def to_launch_command(url):
    """Convert a favourite's URL into a command that executebuiltin can launch.

    A Kodi favourite's text is usually already a builtin (ActivateWindow, PlayMedia, RunAddon…),
    used as-is. script:// is translated to RunAddon; a bare plugin:// path is not a builtin
    (executebuiltin would ignore it), so it is wrapped in RunPlugin so the service at least runs
    it on launch.
    """
    url = normalize_url(url or '')
    if url.lower().startswith('plugin://'):
        return f'RunPlugin("{url}")'
    return url


def delay_label(index):
    if index <= 0:
        return get_string(30461)  # No delay
    return f'{DELAY_VALUES[index]}s' if index < len(DELAY_VALUES) else get_string(30461)


def delay_index(raw):
    """Valid delay index from the raw setting value (text)."""
    try:
        idx = int(raw)
    except (ValueError, TypeError):
        return 0
    return idx if 0 <= idx < len(DELAY_VALUES) else 0


def _strip_tags(text):
    return re.sub(r'\[/?(COLOR[^\]]*|B|I|UPPERCASE|LOWERCASE)\]', '', text).strip()


def _slot_state(i):
    enabled = ADDON.getSetting(f'autofav_{i}_enabled') == 'true'
    title = ADDON.getSetting(f'autofav_{i}_title')
    cmd = ADDON.getSetting(f'autofav_{i}_cmd')
    return enabled, title, cmd, delay_index(ADDON.getSetting(f'autofav_{i}_delay'))


def _pick_favourite(i):
    engine = FavouritesEngine()
    engine.load()
    if not engine.entries:
        xbmcgui.Dialog().notification(get_string(30044), get_string(30468), xbmcgui.NOTIFICATION_WARNING)
        return
    # If the favourite has no name, the command is shown as the label.
    names = [_strip_tags(e.name) or e.url for e in engine.entries]
    current_cmd = ADDON.getSetting(f'autofav_{i}_cmd')
    preselect = next((k for k, e in enumerate(engine.entries) if to_launch_command(e.url) == current_cmd), -1)

    sel = xbmcgui.Dialog().select(get_string(30463), names, preselect=preselect)
    if sel < 0:
        return
    entry = engine.entries[sel]
    ADDON.setSetting(f'autofav_{i}_title', _strip_tags(entry.name) or entry.url)
    ADDON.setSetting(f'autofav_{i}_cmd', to_launch_command(entry.url))
    ADDON.setSetting(f'autofav_{i}_enabled', 'true')
    if not ADDON.getSetting(f'autofav_{i}_delay'):
        ADDON.setSetting(f'autofav_{i}_delay', '0')
    xbmcgui.Dialog().notification(get_string(30459), get_string(30470), xbmcgui.NOTIFICATION_INFO)
    log_audit('AUTOSTART_SET', f'Slot {i}: {entry.url}')


def _pick_delay(i):
    labels = [delay_label(k) for k in range(len(DELAY_VALUES))]
    sel = xbmcgui.Dialog().select(get_string(30462), labels,
                                  preselect=delay_index(ADDON.getSetting(f'autofav_{i}_delay')))
    if sel >= 0:
        ADDON.setSetting(f'autofav_{i}_delay', str(sel))


def _config_slot(i):
    enabled, title, cmd, delay_idx = _slot_state(i)
    if not (enabled and cmd):
        _pick_favourite(i)
        return
    # The dialog heading shows the favourite and its current delay.
    heading = f'{title or cmd} · {delay_label(delay_idx)}'
    opts = [get_string(30465), get_string(30466), get_string(30467), '« ' + get_string(30430)]
    sel = xbmcgui.Dialog().select(heading, opts)
    if sel == 0:
        _pick_favourite(i)
    elif sel == 1:
        _pick_delay(i)
    elif sel == 2:
        ADDON.setSetting(f'autofav_{i}_enabled', 'false')
        xbmcgui.Dialog().notification(get_string(30459), get_string(30471), xbmcgui.NOTIFICATION_INFO)
        log_audit('AUTOSTART_DISABLED', f'Slot {i} disabled')


def run_autostart_menu():
    while True:
        labels = []
        for i in range(1, SLOTS + 1):
            enabled, title, cmd, delay_idx = _slot_state(i)
            if enabled and cmd:
                status = f'{title or cmd} · {delay_label(delay_idx)}'
            else:
                status = get_string(30464)  # Not configured
            labels.append(f'{get_string(30469).format(i)}: {status}')
        labels.append('« ' + get_string(30430))
        labels.append(get_string(30520))

        sel = xbmcgui.Dialog().select(get_string(30459), labels)
        if sel == SLOTS + 1:
            raise CloseAddon()
        if sel < 0 or sel == SLOTS:
            return
        _config_slot(sel + 1)
