"""Guarded network access (§10, D-108, D-131).

Only :mod:`frame_gallery.net.transport` imports networking modules (``socket``,
``ssl``, ``http.client``, ``urllib3``, ``certifi``); every other module works
against the protocols in :mod:`frame_gallery.net.wire`, so the gateway's rules
are tested with fakes and no test touches the network (H2).
"""
