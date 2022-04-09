################## [PATCH] ########################
# basically pass max_msg_size arg to all calls of #
# old_f                                           #
###################################################
import aiohttp
old_f=aiohttp.client.ClientSession.ws_connect
cow = f'\n{" "*12}^__^\n{" "*12}(oo)\\{"_"*7}\n{" "*12}(__)\\{" "*7})\\/\\\n{" "*16}||----w |\n {" w"*5}{" "*5}||{" "*5}||\n'

def new_f(*args, **kwargs):
    print('\n[patching max response size]')
    print(cow)
    if 'max_msg_size' in kwargs.keys():
        print(f":. max_msg_keys: \
            {kwargs['max_msg_keys']} ~> 0")
        del kwargs['max_msg_keys']
    return old_f(max_msg_size=0,*args, **kwargs)

aiohttp.client.ClientSession.ws_connect = new_f
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('connection established')

@sio.event
def my_message(data):

    with open("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/ED2.csv", "rb") as f:
        bytes_read = f.read()
    sio.emit('gg', bytes_read)

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('http://128.46.32.175:8080')
my_message("gg")
sio.wait()