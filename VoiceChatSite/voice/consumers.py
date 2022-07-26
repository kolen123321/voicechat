
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from VoiceChatSite import settings
import asyncio
from voice.instances import Player
from django.core.cache import cache

class ServerConsumer(WebsocketConsumer):

    def connect(self):
        query = self.scope['query_string'].decode()
        for value in query.split("&"):
            if value.split("=")[0] == 'token' and value.split("=")[1] == settings.SERVER_SECRET:
                async_to_sync(self.channel_layer.group_add)(
                    'server',
                    self.channel_name
                )
                self.accept()
                
                return
        self.close()
        

    def disconnect(self, close_code):
        pass


    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == 'join':
            data = {}
            if('data' in data):
                data = text_data_json['data']
            player = Player(text_data_json['uuid'], **data)

            self.send(text_data=json.dumps({
                'type': 'link',
                'forPlayer': text_data_json['uuid'],
                'url': f"?token={player.token}"
            }))
        elif text_data_json['type'] == 'distance':
            data = {
                'type': 'distance_update',
                'hearingDistance': text_data_json['hearingDistance'],
                'distance': json.dumps(text_data_json['distance'])
            }
            cache.set('last_distance', data)
            async_to_sync(self.channel_layer.group_send)(
                'player_data',
                data
            )
        elif text_data_json['type'] == 'disconnect':
            data = {
                'type': 'player_disconnect',
                'uuid': text_data_json['uuid']
            }
            print([plr for plr in Player.get_players() if plr['uuid'] != text_data_json['uuid']])
            cache.set('players', [plr for plr in Player.get_players() if plr['uuid'] != text_data_json['uuid']], timeout=3600)
            async_to_sync(self.channel_layer.group_send)(
                'player_data',
                data
            )
    
    def broadcast_message(self, event):
        data = event['data']
        # Send message to WebSocket
        self.send(text_data=json.dumps(data))
    
class PlayerDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query = self.scope['query_string'].decode()
        for value in query.split("&"):
            if value.split("=")[0] == 'token':
                if Player.get_player(value.split("=")[1]) is not None:
                    self.player = Player.get_player(value.split("=")[1])

                    await self.channel_layer.group_add(
                        'player_data',
                        self.channel_name
                    )

                    await self.accept()
                    await self.channel_layer.group_send('server', {
                        'type': 'broadcast_message',
                        'data': {
                            'type': 'connect',
                            'uuid': self.player['uuid']
                        }
                    })
                    last_distance = cache.get('last_distance')
                    if last_distance is not None:
                        await asyncio.sleep(2)
                        await self.channel_layer.group_send('player_data', last_distance)
                    await self.channel_layer.group_send('player_data', {
                        'type': 'distance_update',
                        'distance': {}
                    })
                    return
        await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_send('server', {
            'type': 'broadcast_message',
            'data': {
                'type': 'disconnect',
                'uuid': self.player['uuid']
            }
        })
        await self.channel_layer.group_discard("chat", self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        pass

    # Receive message from room group
    async def distance_update(self, event):
        
        if 'distance' not in event: return
        
        if type(event['distance']) == dict:
            distance = event["distance"].get(self.player["uuid"])
        else:
            distance = json.loads(event["distance"]).get(self.player["uuid"])
        # Send message to WebSocket
        if distance is not None:
            await self.send(text_data=json.dumps({
                'type': 'distance_update',
                'data': {
                    'hearingDistance': event['hearingDistance'],
                    'distance': distance
                }
            }))
    
    async def player_disconnect(self, event):
        uuid = event['uuid']
        print(uuid == self.player['uuid'])
        if uuid == self.player['uuid']:
            await self.send(text_data=json.dumps({
                'type': 'player_disconnect',
                'data': {
                    'from_uuid': uuid
                }
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'disconnect',
                'data': {
                    'from_uuid': uuid
                }
            }))

class PlayerVoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query = self.scope['query_string'].decode()
        for value in query.split("&"):
            if value.split("=")[0] == 'token':
                if Player.get_player(value.split("=")[1]) is not None:
                    self.player = Player.get_player(value.split("=")[1])

                    await self.channel_layer.group_add(
                        'voice',
                        self.channel_name
                    )

                    await self.accept()

                    return
        await self.close()

    async def disconnect(self, close_code):
        pass

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'join':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'join',
                        'body': {
                            'from_uuid': self.player['uuid']
                        }
                    }
                }
            )
        elif data['type'] == 'offer':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'offer',
                        'body': {
                            'from_uuid': self.player['uuid'],
                            'to_uuid': data['to_uuid'],
                            'offer': data['offer']
                        }
                    }
                }
            )
        elif data['type'] == 'answer':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'answer',
                        'body': {
                            'from_uuid': self.player['uuid'],
                            'to_uuid': data['to_uuid'],
                            'answer': data['answer']
                        }
                    }
                }
            )
        elif data['type'] == 'candidate':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'candidate',
                        'body': {
                            'from_uuid': self.player['uuid'],
                            'to_uuid': data['to_uuid'],
                            'candidate': data['candidate']
                        }
                    }
                }
            )
        elif data['type'] == 'disconnect':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'disconnect',
                        'body': {
                            'from_uuid': self.player['uuid'],
                        }
                    }
                }
            )
        elif data['type'] == 'act_stop':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'act_stop',
                        'body': {
                            'from_uuid': self.player['uuid'],
                        }
                    }
                }
            )
        elif data['type'] == 'act_start':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'act_start',
                        'body': {
                            'from_uuid': self.player['uuid'],
                        }
                    }
                }
            )
        elif data['type'] == 'change_state':
            await self.channel_layer.group_send(
                'voice',
                {
                    'type': 'broadcast_message',
                    'data': {
                        'type': 'change_state',
                        'body': {
                            'from_uuid': self.player['uuid'],
                            **data['states']
                        }
                    }
                }
            )

    # Receive message from room group
    async def broadcast_message(self, event):
        data = event['data']
        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))