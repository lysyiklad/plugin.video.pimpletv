# -*- coding: utf-8 -*-

from resources.lib.pimpletv import PimpleTV

plugin = PimpleTV()


@plugin.action()
def root():
    return plugin.create_listing_()


@plugin.action()
def links(params):
    return plugin.get_links(params)


@plugin.action()
def play(params):
    return plugin.play(params)


@plugin.action()
def reset():
    return plugin.reset()


if __name__ == '__main__':
    plugin.run()
