# -*- coding: utf-8 -*-
"""Startup service.

On Kodi launch:
- Runs the favourites the user configured in the "Auto-start" menu.
- Manages the on-demand web remote server (starts/stops as the
  user toggles it from the main menu).

The monitor loop is lightweight: waitForAbort() is a native sleep,
so CPU usage is effectively 0% when neither feature is active.
"""
import time

import xbmc
import xbmcaddon
import xbmcgui

_ADDON_ID = 'plugin.program.flowfavmanager'
_SLOTS = 3
_DELAY_MAP = [0, 5, 10, 15, 30, 60]
_WIN_PROP = 'flowfavmanager.web_remote.port'


def _log(msg, level=xbmc.LOGINFO):
    xbmc.log(f'[Flow FavManager Service] {msg}', level)


def _parse_delay(raw):
    # The menu stores the index ("0".."5"). We also accept a name in case an old
    # setting holds text; either way, no delay by default.
    try:
        idx = int(raw)
    except (ValueError, TypeError):
        return 0
    return _DELAY_MAP[idx] if 0 <= idx < len(_DELAY_MAP) else 0


def _collect_tasks(addon):
    tasks = []
    for i in range(1, _SLOTS + 1):
        if addon.getSetting(f'autofav_{i}_enabled') != 'true':
            continue
        cmd = addon.getSetting(f'autofav_{i}_cmd').strip()
        if not cmd:
            continue
        tasks.append({'delay': _parse_delay(addon.getSetting(f'autofav_{i}_delay')), 'cmd': cmd})
    tasks.sort(key=lambda t: t['delay'])
    return tasks


def _wait_ready(monitor):
    # Wait until Kodi's startup screen is gone (max. 60 s).
    for _ in range(600):
        if monitor.abortRequested():
            return False
        if not xbmc.getCondVisibility('Window.IsVisible(startup)'):
            return True
        if monitor.waitForAbort(0.1):
            return False
    return not monitor.abortRequested()


def _run_autostart(monitor):
    try:
        addon = xbmcaddon.Addon(_ADDON_ID)
    except RuntimeError:
        _log('Could not load the addon.', xbmc.LOGERROR)
        return

    tasks = _collect_tasks(addon)
    if not tasks:
        return  # nothing configured; return immediately, no waiting

    _log(f'{len(tasks)} favourite(s) queued for autostart.')
    if not _wait_ready(monitor):
        return

    # Delays are absolute from the moment Kodi is ready (t0), not cumulative. The queue is
    # sorted by delay, so a favourite with a short delay does not wait for one with a longer delay.
    t0 = time.time()
    for task in tasks:
        if monitor.abortRequested():
            break
        remaining = task['delay'] - (time.time() - t0)
        if remaining > 0 and monitor.waitForAbort(remaining):
            break
        if monitor.abortRequested():
            break
        xbmc.executebuiltin(task['cmd'])
        _log(f'Launched: {task["cmd"]}')


def _get_web_port(addon):
    try:
        return int(addon.getSetting('web_remote_port') or '8080')
    except ValueError:
        return 8080


def _main():
    monitor = xbmc.Monitor()
    try:
        addon = xbmcaddon.Addon(_ADDON_ID)
    except RuntimeError:
        _log('Could not load the addon.', xbmc.LOGERROR)
        return

    # Defensive import: if web_remote fails to load (e.g. syntax error during
    # development), autostart still works and we just log the error.
    web_remote = None
    try:
        from resources.lib import web_remote as _wr
        web_remote = _wr
    except Exception as e:
        _log(f'Could not load web_remote module: {e}', xbmc.LOGERROR)

    win = xbmcgui.Window(10000)  # Home window — properties survive across plugin invocations

    def _sync():
        if web_remote is None:
            return
        enabled = addon.getSetting('web_remote_enabled') == 'true'
        if enabled and not web_remote.is_running():
            port = web_remote.start(_get_web_port(addon))
            win.setProperty(_WIN_PROP, str(port) if port else '')
            if not port:
                _log('All ports busy; web remote unavailable.', xbmc.LOGWARNING)
        elif not enabled and web_remote.is_running():
            web_remote.stop()
            win.clearProperty(_WIN_PROP)

    _sync()             # start server now if already enabled before this Kodi session
    _run_autostart(monitor)

    while not monitor.abortRequested():
        if monitor.waitForAbort(2):
            break
        _sync()

    if web_remote is not None:
        web_remote.stop()
    win.clearProperty(_WIN_PROP)


_main()
