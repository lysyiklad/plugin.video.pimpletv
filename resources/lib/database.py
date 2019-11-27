# -*- coding: utf-8 -*-

# https://github.com/coleifer/peewee/blob/master/examples/hexastore.py

import os
import datetime
import xbmcaddon
import xbmc


from .peewee import *

__addon__ = xbmcaddon.Addon()
__profile_dir__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
#__profile_dir__ = '/home/kvm/.kodi/userdata/addon_data/plugin.video.pimpletv'

db = SqliteDatabase(os.path.join(__profile_dir__, 'match.db'), pragmas={'foreign_keys': 1})
#db = SqliteDatabase('/home/kvm/.kodi/userdata/addon_data/plugin.video.pimpletv/match.db', pragmas={'foreign_keys': 1})


class Match(Model):
    time = DateTimeField(default=datetime.datetime.now())  # время сканирования
    # хэш матча формируемый из match + date_time
    id = IntegerField(primary_key=True)
    match = TextField()  # "Динамо Киев - Шахтер"
    league = TextField(default='')  # лига, соревнование
    date_broadcast = DateTimeField(
        default=datetime.datetime.now())  # время и дата матча
    title = TextField(default='')  # описание матча
    label = TextField(default='')  # метка, которая отображается в списке

    url_home_logo = TextField(default='')  # ссылка на лого хозяев
    url_away_logo = TextField(default='')  # ссылка на лого гостей

    thumb = TextField(default='')
    fanart = TextField(default='')
    clearart = TextField(default='')
    poster = TextField(default='')
    icon = TextField(default='')
    url_links = TextField(default='')  # ссылка на страницу с видео

    class Meta:
        database = db

    # Добавить матч в БД
    @staticmethod
    def addMatch(**kwargs):
        try:
            Match.create(
                time=kwargs['time'],
                id=kwargs['id'],
                match=kwargs['match'],
                league=kwargs['league'],
                date_broadcast=kwargs['date_broadcast'],
                thumb=kwargs['thumb'],
                poster=kwargs['poster'],
                fanart=kwargs['fanart'],
                icon=kwargs['icon'],
                url_links=kwargs['url_links'],
            )
        except IntegrityError as e:
            print(e)

    @staticmethod
    def getMatches():
        return Match.select().order_by(Match.date_broadcast)

    # Возвращаем матч
    @staticmethod
    def getMatch(id):
        try:
            return Match.get(Match.id == id)
        except Exception as e:
            return None

    # Удалить матч из БД
    @staticmethod
    def deleteMatch(id):
        match = Match.get(Match.id == id)
        match.delete_instance()

    @staticmethod
    def dateScan():
        return Match.select().order_by(Match.time.desc())[0].time

    # Возвращаем ссылку на страницу со ссылками
    @staticmethod
    def getUrlHref(id):
        try:
            return Match.get(Match.id == id).url_links
        except Exception as e:  # LinkDoesNotExist
            print(type(e))
            return None


class Link(Model):
    title = TextField()
    kbps = TextField()
    resol = TextField()
    href = TextField()
    match = ForeignKeyField(Match, on_delete='cascade', on_update='cascade')

    class Meta:
        database = db
        primary_key = CompositeKey('href', 'match')

    # Проверить наличие ссылок в матче
    @staticmethod
    def getHrefMatch(id):
        try:
            link_model = Link.select().where(Link.match == id)
            links = []
            for l in link_model:
                links.append(
                    {
                        'id': id,
                        'title': l.title,
                        'kbps': l.kbps,
                        'resol': l.resol,
                        'href': l.href,
                    })
            return links if links else None
        except Exception as e:  # LinkDoesNotExist
            print(type(e))
            return None

    # Добавить ссылки в определенный матч
    @staticmethod
    def addLink(id, links):
        exist = True
        try:
            match = Match.get(Match.id == id)
        except DoesNotExist as de:
            exist = False

        if exist:
            for link in links:
                try:
                    Link.create(
                        title=link['title'],
                        kbps=link['kbps'],
                        resol=link['resol'],
                        href=link['href'],
                        match=match,
                    )
                except Exception as e:
                    print(e)
                    continue


db.create_tables([Match, Link])
