# -*- coding: utf-8 -*-

# https://github.com/coleifer/peewee/blob/master/examples/hexastore.py

import os
# import sys
import datetime

# file_dir = os.path.dirname(__file__)
# sys.path.append(file_dir)
#
# import os.path
import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# from peewee import *

from .peewee import *

print 'ddddddddddddddddddddddddddddddddddddddddddddd'

class DB(object):
    def __init__(self, plugin):
        self._plugin = plugin
        self.db = SqliteDatabase(os.path.join(self._plugin.userdata(), 'match.db'), pragmas={'foreign_keys': 1})
        #self.db = SqliteDatabase(os.path.join(self._plugin.userdata(), 'match.db'))

        self.match = self.get_model_match()
        self.link = self.get_model_link()
        self._plugin.log('****************** %s --- %s' %
                         (os.path.join(self._plugin.userdata(), 'match.db'), self.get_match(668941931662562689)))
        # for m in self.match.select():
        #     self._plugin.log('*********m.id********* %s' % type(m))


    def get_model_match(self):
        class Match(Model):
            time = DateTimeField(default=datetime.datetime.now())  # время сканирования
            id = IntegerField(primary_key=True)  # хэш матча формируемый из match + date_time
            match = TextField()  # "Динамо Киев - Шахтер"
            league = TextField(default='')  # лига, соревнование
            date_broadcast = DateTimeField(default=datetime.datetime.now())  # время и дата матча
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
                database = self.db

        self.db.create_tables([Match])
        return Match

    def get_model_link(self):
        class Link(Model):
            title = TextField()
            kbps = TextField()
            resol = TextField()
            href = TextField()
            match = ForeignKeyField(self.match, on_delete='cascade', on_update='cascade')

            class Meta:
                database = self.db
                primary_key = CompositeKey('href', 'match')

        self.db.create_tables([Link])
        return Link

    # Добавить матч в БД
    def add_match(self, **kwargs):
        try:
            self.match.create(
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

    # Проверить есть ли матч в бд
    def get_match(self, id):
        try:
            return self.match.get(self.match.id == id)
        except Exception as e:
            return None

    def get_matches(self):
        # ms = self.match.select()
        # for m in ms:
        #     print m.id
        return self.match.select() #.order_by(self.match.date_broadcast)

    # Удалить матч из БД
    def delete_match(self, id):
        match = self.match.get(self.match.id == id)
        match.delete_instance()

    def date_scan(self):
        return self.match.select().order_by(self.match.time.desc())[0].time

    # Добавить ссылки в определенный матч
    def add_link(self, id, links):
        exist = True
        try:
            match = self.match.get(self.match.id == id)
        except DoesNotExist as de:
            exist = False

        if exist:
            for link in links:
                try:
                    self.link.create(
                        title=link['title'],
                        kbps=link['kbps'],
                        resol=link['resol'],
                        href=link['href'],
                        match=match,
                    )
                except Exception as e:
                    print(e)
                    continue

    # Возвращаем ссылку на страницу со ссылками
    def get_url_href(self, id):
        try:
            return self.match.get(self.match.id == id).url_links
        except Exception as e:  # LinkDoesNotExist
            print(type(e))
            return None

    # Проверить наличие ссылок в матче
    def get_href_match(self, id):
        try:
            link_model = self.link.select().where(self.link.match == id)
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
