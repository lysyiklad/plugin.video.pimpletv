# -*- coding: utf-8 -*-
import os
import json
import urllib2
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib

from resources.lib.pimpletv import PimpleTV
from resources.lib.plugin import PimpletvPlugin

# from simpleplugin import RoutedPlugin
# plugin = RoutedPlugin()


# @plugin.route('/')
# def root():
#     listing = get_releases_list()
#     return plugin.create_listing(listing, content='movies', sort_methods=(xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING), cache_to_disk=True)


# ID_PLUGIN = 'plugin.video.pimpletv'
# __addon__ = xbmcaddon.Addon(id=ID_PLUGIN)
# __path__ = __addon__.getAddonInfo('path')

# addon = xbmcaddon.Addon()
# addon_path = addon.getAddonInfo('path')
# addonID = addon.getAddonInfo('id')


plugin = PimpletvPlugin()

pimpletv = PimpleTV(plugin)


@plugin.action()
def root():
    #matches = get_matches()
    select_item = [{'label': '[COLOR FF0084FF][B]ВЫБРАТЬ ТУРНИРЫ[/B][/COLOR]',
                    'url': plugin.get_url(action='select_matches')},
                   {'label': '[COLOR FF0084FF][B]ОБНОВИТЬ[/B][/COLOR]',
                    'url': plugin.get_url(action='update_cache')}, ]
    #return plugin.create_listing(select_item + matches, content='tvseries',
    #                              view_mode=55, sort_methods={'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '% J'})
    plugin.log(list(pimpletv.matches()))
    return pimpletv.matches()


if __name__ == '__main__':
    plugin.run()


# pimpletv.update()
# # pimpletv.print_db()

# #matchs = list(pimpletv.matches())

# for m in pimpletv.matches():
#     # print(m['label'])
#     # print(m['url'])
#     print(m['info']['video']['plot'])

# # links = pimpletv.get_href_match(1693642698)
# #
# # print(links)

# # matchs = pimpletv._db.match.select()
# #
# # for m in matchs:
# #     print(m.match)
# #
# # links = pimpletv._db.link.select()
# #
# # for l in links:
# #     print(l.match, l.title, l.href, l.kbps)
