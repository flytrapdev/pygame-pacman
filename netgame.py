import json
from socket import *
from globals import MAZE_WIDTH, MAZE_HEIGHT, GHOST_NAMES, BUFSIZE, NET_HOST, net_settings, game_settings
from select import select

class ConnectionData:
    def __init__(self):
        self.data = {'type':'connection'}

    def encode(self):
        return json.dumps(self.data)

class SettingsData:
    def __init__(self, data = game_settings):
        self.data = data

    def encode(self):
        return json.dumps(self.data)

class AcknowledgeData:
    def __init__(self):
        self.data = {'type':'ack'}

    def encode(self):
        return json.dumps(self.data)

class DataAcknowledgeData:
    def __init__(self, header='', content=[], data={}):
        if len(data)>0:
            self.header = data['header']
            self.content = data['content']
        else:
            self.header = header
            self.content = content

    def encode(self):
        d = {'type':'data_ack', 'header':self.header, 'content':self.content}
        return json.dumps(d)

class SkinData:
    def __init__(self, skin=(0,0), data={}):
        if len(data)>0:
            self.skin = data['skin']
        else:
            self.skin = skin

    def encode(self):
        d = {'type':'skin', 'skin':self.skin}
        return json.dumps(d)

class MazeChangeData:
    def __init__(self, maze=game_settings['maze'], maze_count=game_settings['maze_count'], data={}):
        if len(data)>0:
            self.maze = data['maze']
            self.maze_count = data['maze_count']
        else:
            self.maze = maze
            self.maze_count = maze_count

    def encode(self):
        d = {'type':'start', 'maze':self.maze, 'maze_count':self.maze_count}
        return json.dumps(d)


class PlayerData:
    def __init__(self, x=0, y=0, spd=0, dir=0, anim=0, skin=(0,0), dead=False, score=-1,\
        lives=3, dots=[], ghosts=[], show_points=0, ready=False, data={}):
        '''Decode dict or copy arguments'''
        if len(data)>0:
            self.x, self.y = data['x'], data['y']
            self.dir = data['dir']
            self.spd = data['spd']
            self.skin = data['skin']
            self.dead = data['dead']
            self.anim = data['anim']
            self.score = data['score']
            self.lives = data['lives']
            self.dots = data['dots']
            self.ghosts = data['ghosts']
            self.show_points = data['show_points']
            self.ready = data['ready']
        else:
            self.score = score
            self.dots = dots
            self.x = x
            self.y = y
            self.spd = spd
            self.dir = dir
            self.skin = skin
            self.dead = dead
            self.anim = anim
            self.lives = lives
            self.ghosts = ghosts
            self.show_points = show_points
            self.ready = ready

        # Check if data is correct
        if any(len(d)!=2 for d in dots):
            raise ValueError

    def encode(self):
        d = {'type':'player','x':self.x, 'y':self.y, 'spd':self.spd, 'dir':self.dir, 'anim':self.anim, 'skin':self.skin,\
            'dead':self.dead, 'score':self.score, 'lives':self.lives, 'dots':self.dots, 'ghosts':self.ghosts,\
            'show_points':self.show_points, 'ready':self.ready}
        return json.dumps(d)

class GhostData:
    def __init__(self, x=0, y=0, spd=0, dir=0, anim=0, state='', show_points=0, siren=False,\
    scared_clock=360, name='', data={}):

        if len(data)>0:
            self.x, self.y = data['x'], data['y']
            self.dir = data['dir']
            self.spd = data['spd']
            self.anim = data['anim']
            self.state = data['state']
            self.show_points = data['show_points']
            self.name = data['name']
            self.siren = data['siren']
            self.scared_clock = data['scared_clock']
        else:
            self.x, self.y = x, y
            self.spd = spd
            self.dir = dir
            self.anim = anim
            self.state = state
            self.show_points = show_points
            self.name = name
            self.siren = siren
            self.scared_clock = scared_clock

    def encode(self):
        d = {'type':'ghost', 'x':self.x, 'y':self.y, 'spd':self.spd, 'dir':self.dir, 'anim':self.anim,\
            'state':self.state, 'show_points':self.show_points, 'siren':self.siren, 'scared_clock':self.scared_clock,\
            'name':self.name}
        return json.dumps(d)


class GameData:
    def __init__(self, score=[], dots={}, data={}):
        if len(data)>0:
            self.score = data['score']
            self.dots = data['dots']
        else:
            self.score = score
            self.dots = dots

        # Check if data is correct
        if ['total', 'eaten'] not in self.dots.keys():
            raise ValueError

    def encode(self):
        d = {'type':'game','score':self.score, 'dots':self.dots}
        return json.dumps(d)

class Netgame:
    def __init__(self, addr=('127.0.0.1',5555)):
        self.addr = addr

    def net_read(self):
        '''Return a list of received objects from socket'''
        inputready, outputready, exceptready = select([self.sock],[self.sock],[])
        result = []

        while len(inputready) > 0:
            for s in inputready:
                received, addr = s.recvfrom(BUFSIZE)
                # If host, save server address
                if net_settings['type'] == NET_HOST:
                    self.addr = addr
                # Read received data
                if received != b'':
                    d = json.loads(received.decode())
                    # Add unpacked object to result
                    result.append(unpack(d))

            inputready, outputready, exceptready = select([self.sock],[self.sock],[])

        return result

    def net_send(self,data):
        '''Send data to socket'''
        inputready, outputready, exceptready = select([self.sock],[self.sock],[])

        for s in outputready:
            str = data.encode()
            s.sendto(str.encode(), self.addr)

    def close(self):
        '''Close socket'''
        self.sock.close()


class Host(Netgame):
    def __init__(self, addr=('127.0.0.1',5555)):
        super().__init__(addr)
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(self.addr)

    def get_name(self):
        return self.sock.getsockname()

class Join(Netgame):
    def __init__(self, addr=('127.0.0.1',5555)):
        super().__init__(addr)
        self.sock = socket(AF_INET, SOCK_DGRAM)

    def get_name(self):
        return self.addr

def unpack(dat):
    '''Return the object created from the encoded data'''
    if dat['type'] == 'connection':
        return ConnectionData()
    elif dat['type'] == 'ack':
        return AcknowledgeData()
    elif dat['type'] == 'data_ack':
        return DataAcknowledgeData(data = dat)
    elif dat['type'] == 'skin':
        return SkinData(data = dat)
    elif dat['type'] == 'start':
        return MazeChangeData(data = dat)
    elif dat['type'] == 'settings':
        return SettingsData(data = dat)
    elif dat['type'] == 'player':
        return PlayerData(data = dat)
    elif dat['type'] == 'ghost':
        return GhostData(data = dat)
    elif dat['type'] == 'game':
        return GameData(data = dat)
    return dat
