# -*- coding: utf-8 -*-
"""Quick dialog-based editor (no graphical window): move, rename and delete favourites."""
import xbmc
import xbmcgui

from resources.lib.common import get_string
from resources.lib.database import FavouritesEngine


def move_target(action, idx, total):
    """Destination index for the fixed move actions (up/down N, top, bottom)."""
    targets = {
        0: max(0, idx - 1),
        1: min(total - 1, idx + 1),
        2: max(0, idx - 5),
        3: min(total - 1, idx + 5),
        4: 0,
        5: total - 1,
    }
    return targets.get(action, idx)


def run_simple_editor():
    engine = FavouritesEngine()
    engine.load()
    entries = engine.entries

    while True:
        if not entries:
            xbmcgui.Dialog().ok(get_string(30368), get_string(30369))
            return

        names = [f"{i + 1}. {e.name}" for i, e in enumerate(entries)]
        idx = xbmcgui.Dialog().select(get_string(30384), names)
        if idx == -1:
            return

        selected_entry = entries[idx]
        actions = [
            get_string(30390), get_string(30391), get_string(30408), get_string(30409),
            get_string(30410), get_string(30411), get_string(30392),
            get_string(30112), get_string(30119),
        ]
        action = xbmcgui.Dialog().select(get_string(30385).format(selected_entry.name), actions)
        if action == -1:
            continue

        changed = False
        new_idx = idx

        if action <= 5:
            new_idx = move_target(action, idx, len(entries))
        elif action == 6:  # Move to a specific position
            kb = xbmc.Keyboard('', get_string(30393).format(len(entries)))
            kb.doModal()
            if kb.isConfirmed() and kb.getText().isdigit():
                new_idx = max(0, min(len(entries) - 1, int(kb.getText()) - 1))
            else:
                continue

        if action <= 6 and new_idx != idx:
            entries.pop(idx)
            entries.insert(new_idx, selected_entry)
            changed = True
        elif action == 7:  # Rename
            kb = xbmc.Keyboard(selected_entry.name, get_string(30160))
            kb.doModal()
            if kb.isConfirmed() and kb.getText():
                selected_entry.name = kb.getText()
                changed = True
        elif action == 8:  # Delete
            if xbmcgui.Dialog().yesno(get_string(30167), get_string(30168).format(selected_entry.name)):
                entries.pop(idx)
                changed = True

        if changed:
            engine.save(engine.generate_xml(entries))
            xbmcgui.Dialog().notification(get_string(30243), get_string(30244), xbmcgui.NOTIFICATION_INFO, 1000)
