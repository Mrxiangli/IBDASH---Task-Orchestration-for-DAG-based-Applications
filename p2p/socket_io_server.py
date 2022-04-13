

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

import eventlet
import socketio

sio = socketio.AsyncServer()
app = aiohttp.web.Application()
sio.attach(app)

# sio = socketio.Server()
# app = socketio.WSGIApp(sio, static_files={
#     '/': {'content_type': 'text/html', 'filename': 'index.html'}
# })

@sio.event
def connect(sid, environ):
    print('connect ', sid)

@sio.event
def gg(sid, data):
    #print('message ', data)
    print(len(data))

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == '__main__':
    # eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    aiohttp.web.run_app(app)