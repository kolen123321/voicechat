import string
from django.db import models
import jwt, time, random
from VoiceChatSite import settings
from django.core.cache import cache

class Player:
    
    @classmethod
    def get_players(cls):
        return cache.get('players')


    def get_player(token):
        
        for plr in Player.get_players():
            if plr['token'] == token:
                return plr
        return None

    uuid = ...
    token = ...
    is_staff = ...

    def __init__(self, uuid, is_staff=False, token=None) -> None:
        self.uuid = uuid
        if token is None:
            self.token = ''.join([random.choice(string.ascii_letters) for i in range(5)])
        else:
            self.token = token
        self.is_staff = is_staff
        all_players = cache.get('players')
        all_players.append(self.__dict__)
        cache.set('players', all_players, timeout=3600 * 24)

    
