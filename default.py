# -*- coding: utf-8 -*-
"""Plugin entry point: check the security gate, then hand off to the router."""
import sys

from resources.lib.security import check_security_gate

if __name__ == '__main__':
    if not check_security_gate():
        import xbmcplugin
        from resources.lib.common import PLUGIN_ID
        if PLUGIN_ID >= 0:
            xbmcplugin.endOfDirectory(PLUGIN_ID, succeeded=False)
    else:
        from resources.lib.router import route
        full_url = sys.argv[0]
        if len(sys.argv) > 2:
            full_url += sys.argv[2]
        route(full_url)
