# -*- coding: utf-8 -*-

class DBCache(object):
    __db_cache = []
    __update_flag = False

    @staticmethod
    def is_updated():
        return DBCache.__update_flag

    @staticmethod
    def get_cache():
        return DBCache.__db_cache

    @staticmethod
    def set_update_flag(flag):
        DBCache.__update_flag = flag

    @staticmethod
    def update_cache(new_contents):
        DBCache.__db_cache = new_contents
        DBCache.set_update_flag(False)
