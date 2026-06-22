# -*- coding: utf-8 -*-
"""Global context menu: adds the selected Kodi item to a Flow FavManager profile."""
import xbmc
import xbmcgui

from resources.lib.common import get_string, log_debug
from resources.lib.database import FavouriteEntry, get_profiles, load_profile, save_profile
from resources.lib.listing import normalize_url


def get_selected_item_info():
    """Data of the currently selected Kodi ListItem (name, thumbnail, path)."""
    name = xbmc.getInfoLabel('ListItem.Label')
    thumb = xbmc.getInfoLabel('ListItem.Thumb') or xbmc.getInfoLabel('ListItem.Icon')
    url = (xbmc.getInfoLabel('ListItem.FileNameAndPath')
           or xbmc.getInfoLabel('ListItem.Path')
           or xbmc.getInfoLabel('ListItem.FolderPath'))
    return name, thumb, url


def _create_profile_with(name, thumb, url):
    kb = xbmc.Keyboard(get_string(30034), get_string(30035))
    kb.doModal()
    if not kb.isConfirmed() or not kb.getText():
        return
    profile_name = kb.getText()
    if save_profile(profile_name, [FavouriteEntry(name, thumb, url)]):
        xbmcgui.Dialog().notification(get_string(30036), get_string(30037).format(name, profile_name), xbmcgui.NOTIFICATION_INFO)


def _add_to_existing(profile, name, thumb, url):
    try:
        existing = load_profile(profile['filename'])
    except (OSError, ValueError) as e:
        log_debug(f'Error loading profile: {e}')
        xbmcgui.Dialog().notification(get_string(30044), get_string(30046), xbmcgui.NOTIFICATION_ERROR)
        return

    if any(entry.url == url for entry in existing):
        xbmcgui.Dialog().notification(get_string(30040), get_string(30041).format(name, profile['name']), xbmcgui.NOTIFICATION_INFO)
        return

    existing.append(FavouriteEntry(name, thumb, url))
    if save_profile(profile['name'], existing):
        xbmcgui.Dialog().notification(get_string(30042), get_string(30043).format(name[:20], profile['name']), xbmcgui.NOTIFICATION_INFO, 3000)
        log_debug(f"'{name}' added to {profile['name']}")
    else:
        xbmcgui.Dialog().notification(get_string(30044), get_string(30045), xbmcgui.NOTIFICATION_ERROR)


def main():
    name, thumb, url = get_selected_item_info()
    url = normalize_url(url)
    if not name or not url:
        xbmcgui.Dialog().notification(get_string(30030), get_string(30031), xbmcgui.NOTIFICATION_WARNING)
        return

    profiles = get_profiles()
    if not profiles:
        if xbmcgui.Dialog().yesno(get_string(30032), get_string(30033)):
            _create_profile_with(name, thumb, url)
        return

    profile_names = [p['name'] for p in profiles]
    profile_names.append(get_string(30038))  # + Create new profile
    sel = xbmcgui.Dialog().select(get_string(30039).format(name[:30]), profile_names)
    if sel < 0:
        return
    if sel == len(profiles):
        _create_profile_with(name, thumb, url)
    else:
        _add_to_existing(profiles[sel], name, thumb, url)


if __name__ == '__main__':
    main()
