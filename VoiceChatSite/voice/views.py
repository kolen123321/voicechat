from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import exceptions
from .instances import Player
import json
from django.core.cache import cache


if cache.get('players') == None:
    cache.set('players', [], timeout=3600 * 24)

player = Player('93877f60-4c7b-446f-88e0-e7d710177346')
player.token = 'token1'

player = Player('6b16b894-a1e5-4e59-a9eb-8d9dc7edd586')
player.token = 'token2'

player = Player('12c05a88-4c8f-4d75-ae54-b5964eee6d90')
player.token = 'token3'


class VoiceView(APIView):

    def get(self, request):
        

        if 'token' not in request.GET:
            raise exceptions.APIException('Error')
        player_data = Player.get_player(request.GET['token'])
        if player_data is None:
            return Response({
                'detail': 'Player not found'
            }, status=404)
        player = Player(**player_data)
        return Response({
            'uuid': player.uuid,
            'token': player.token
        })
        
