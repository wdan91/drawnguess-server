#!/usr/bin/env python

from flask import Flask, render_template, jsonify, request, g
from flask_socketio import SocketIO, join_room, leave_room, emit
import hashlib, time, MySQLdb, MySQLdb.cursors

class MyDB:
    db = None
    cursor = None
    def __init__(self):
        self.connect()
        return
    def connect(self):
        self.db = MySQLdb.connect(
            host="localhost",
            port=3306,
            user="root",
            passwd="password",
            db="mobile",
            use_unicode=True,
            charset="utf8",
            cursorclass=MySQLdb.cursors.DictCursor
            )
        self.cursor = self.db.cursor()
        return

app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
m = hashlib.md5()

@app.before_request
def before_request():
    g.mydb = MyDB()
    return

@app.teardown_request
def teardown_request(exception):
    mydb = getattr(g,"mydb",None)
    if mydb is not None:
        mydb.db.close()
        mydb.cursor = None
    return


@app.route("/get_room_id", methods=["POST"])
def get_room_id():    
    user_id = request.form.get("user_id")
    hstring = user_id + str(time.time())
    print hstring
    m.update(hstring)
    print m.hexdigest()
    return jsonify(status="OK", data={"room_id":m.hexdigest()})

@app.route("/get_puzzle", methods=["POST"])
def get_puzzle():
    query = "SELECT * FROM puzzles ORDER BY rand() LIMIT 1"
    g.mydb.cursor.execute(query)
    result=g.mydb.cursor.fetchone()
    return jsonify(status="OK", data=result)


@socketio.on('join_waiting_room')
def on_wr_join(data):
    user_id = data['user_id']
    room_id = data['room_id']
    join_room(room_id)
    try:
        ulist = socketio.server.manager.rooms['/'][room_id]
        print ulist
    except KeyError:
        ulist = {}
        print ulist
    data['sdata'] = {}
    data['sdata']['user_list'] = ulist.keys()
    data['sdata']['user_sid'] = request.sid
    print (user_id + " joined waiting room "+ room_id )
    emit('join_waiting_room_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('member_update')
def on_mem_update(data):
    user_id = data['user_id']
    room_id = data['room_id']
    try:
        ulist = socketio.server.manager.rooms['/'][room_id]
        print ulist
    except KeyError:
        ulist = {}
        print ulist
    data['sdata'] = {}
    data['sdata']['user_list'] = ulist.keys()
    print (user_id + " ask for updating status")
    emit('member_update_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('game_join')
def on_game_join(data):
    user_id = data['user_id']
    room_id = data['room_id']
    print (user_id + " ask for preparing game")
    emit('game_join_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('leave_waiting_room')
def on_wr_leave(data):
    user_id = data['user_id']
    room_id = data['room_id']
    leave_room(room_id)
    print(user_id + ' has left the waiting room '+ room_id)
    emit('leave_waiting_room_broadcasting', data, room=room_id, broadcast=True)


@socketio.on('join_room')
def on_join(data):
    user_id = data['user_id']
    room_id = data['room_id']
    join_room(room_id)
    try:
        ulist = socketio.server.manager.rooms['/'][room_id]
        print ulist
    except KeyError:
        ulist = {}
        print ulist
    data['sdata'] = {}
    data['sdata']['user_list'] = ulist.keys()
    data['sdata']['user_sid'] = request.sid
    print (user_id + " joined room "+ room_id )
    emit('join_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('game_ready')
def on_game_ready(data):
    user_id = data['user_id']
    room_id = data['room_id']
    print (user_id + " is ready for game")
    emit('game_ready_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('pos_update')
def on_pos_update(data):
    user_id = data['user_id']
    room_id = data['room_id']
    print (user_id + " update drawing positions")
#    print data["data"]
    emit('pos_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('message_send')
def on_msg_send(data):
    user_id = data['user_id']
    room_id = data['room_id']
    print (user_id + " send a message")
    print data['data']['message']
    emit('message_send_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('game_finish')
def on_game_finish(data):
    user_id = data['user_id']
    room_id = data['room_id']
    print (user_id + " ask for finishing game")
    emit('game_finish_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('game_quit')
def on_game_quit(data):
    user_id = data['user_id']
    room_id = data['room_id']
    print (user_id + " ask for quiting game")
    emit('game_quit_broadcasting', data, room=room_id, broadcast=True)

@socketio.on('leave_room')
def on_leave(data):
    user_id = data['user_id']
    room_id = data['room_id']
    leave_room(room_id)
    print(user_id + ' has left the room '+ room_id)
    emit('leave_broadcasting', data, room=room_id, broadcast=True)


if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0',port=8000)
