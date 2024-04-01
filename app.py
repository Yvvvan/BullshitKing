import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 游戏用参数
clients = {}
connects = []

# 结构 {'username': {'client_id': 'xxx', 'role': 'xxx'}}
assignRole = False
smartPlayer = None
honestPlayer = None
startGame = False
playerLimit = 2
playerListUpdated = False
selectedWord = None

wordDataBase = [
    {'word': '模拟词语',
     'difficulty': 1,
     'hint': '提示/词语/啊',
     'story': '模拟词语是我在做这个游戏的时候用来模拟的词语。',
     },
]


def client_id_to_usename(client_id):
    for username in clients:
        if clients[username]['client_id'] == client_id:
            return username
    return False


def number_players():
    count = 0
    for user in clients:
        if clients[user]['client_id'] is not None:
            count += 1
    return count


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    # print(f'Client connected: {request.sid}')
    connects.append(request.sid)
    emit('system_message', {'client': request.sid, 'message': '请输入一个用户名'}, room=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    # print(f'Client disconnected: {request.sid}')
    username = client_id_to_usename(request.sid)
    connects.remove(request.sid)
    if username:
        clients[username]['client_id'] = None
        emit('system_message', {'client': request.sid, 'message': f'{username}已离开'}, broadcast=True)


@socketio.on('message_from_client')
def handle_message(message):
    global assignRole, smartPlayer, honestPlayer, startGame, playerLimit, playerListUpdated, selectedWord

    client_id = request.sid
    # print(f'Client ID: {client_id}, Message: {message}')

    # 用户名处理， 第一条消息 (=当client_id 没有被记录时)
    if not client_id_to_usename(client_id):
        userName = message
        if userName not in clients:
            clients[userName] = {'client_id': client_id, 'role': None}
            emit('system_message', {'client': client_id, 'message': f'{userName}已加入'}, broadcast=True)
            join_after_start(userName)

        elif userName in clients and clients[userName]['client_id'] is None:
            clients[userName]['client_id'] = client_id
            emit('system_message', {'client': client_id, 'message': f'{userName}已重连'}, broadcast=True)
            reconnect_after_start(userName)

        elif userName in clients and clients[userName]['client_id'] is not None:
            emit('system_message', {'client': client_id, 'message': f'{userName}已被占用，请重新输入'}, room=client_id)
            return

        else:
            emit('system_message', {'client': client_id, 'message': '未知错误'}, room=client_id)
            return

    else:
        if message == '!!start' and not startGame:
            if number_players() < playerLimit:
                emit('system_message', {'client': client_id, 'message': '人数不足'}, room=client_id)
                return
            else:
                emit('system_message', {'client': client_id, 'message': '游戏开始'}, broadcast=True)
                startGame = True
                start_game()
                return
        elif message == '!!end' and startGame:
            emit('system_message', {'client': client_id, 'message': '游戏结束'}, broadcast=True)
            startGame = False
            assignRole = False
            playerListUpdated = True
            for user in clients:
                clients[user]['role'] = None
            return
        else:
            emit('player_message', {'client': client_id, 'username': client_id_to_usename(client_id),
                                    'message': message}, broadcast=True)
            return


def start_game():
    # 移除所有没有输入用户名的connection
    to_be_checked = connects.copy()
    for connect in to_be_checked:
        if not client_id_to_usename(connect):
            emit('system_message', {'client': connect, 'message': '游戏已开始，由于未输入用户名，已断开连接'}, room=connect)
            disconnect(connect)


    # 安排游戏逻辑
    emit('game_message', {'client': None, 'message': '============='}, broadcast=True)
    global assignRole, smartPlayer, honestPlayer, startGame, playerLimit, playerListUpdated, selectedWord
    if not assignRole and startGame:
        assignRole = True
        # 从mydict中随机选择一个key
        player_1 = random.choice(list(clients.keys()))  # 大聪明
        while clients[player_1]['client_id'] is None:
            player_1 = random.choice(list(clients.keys()))
        player_2 = player_1  # 老实人
        while player_1 == player_2 or clients[player_2]['client_id'] is None:
            player_2 = random.choice(list(clients.keys()))
        smartPlayer = player_1
        honestPlayer = player_2
        # 这个player是“大聪明” 其他人是“瞎掰人”
        for i in clients:
            if clients[i]['client_id'] is not None:
                if i == player_1:
                    clients[i]['role'] = 'smart'
                elif i == player_2:
                    clients[i]['role'] = 'honest'
                else:
                    clients[i]['role'] = 'liar'

        # 把大聪明的名字发给所有人
        emit('game_message', {'client': clients[player_1]['client_id'], 'message': f'{player_1}是大聪明!'},
             broadcast=True)

        # 在wordDataBase中随机选择一个词语，把词语发给所有人
        word = random.choice(wordDataBase)
        selectedWord = word

        emit('game_message', {'client': clients[player_1]['client_id'],
                              'message': f'\n词语： {word["word"]}'
                                         f'\n难度： {word["difficulty"]}'
                                         f'\n提示： {word["hint"]}'}, broadcast=True)

        # 把词语的store发给老实人，把“开编”发送给瞎掰人
        for i in clients:
            if clients[i]['client_id'] is not None:
                if i == player_1:
                    message = '【你是大聪明】：给出一个倒计时信号！'
                elif i == player_2:
                    message = '【你是老实人】：故事：' + word['story']
                else:
                    message = '【你是瞎掰人】：请准备瞎掰！'
            emit('game_message', {'client': clients[i]['client_id'],
                                  'message': message},
                 broadcast=False, room=clients[i]['client_id'])

        # print('大聪明是：', player_1)
        # print('老实人是：', player_2)
        # print('词语是：', word['word'], '，提示是：', word['hint'], '，故事是：', word['story'], '，难度是：', word['difficulty'])


def reconnect_after_start(userName):
    global assignRole, smartPlayer, honestPlayer, startGame, playerLimit, playerListUpdated, selectedWord
    word = selectedWord
    if startGame and clients[userName]['client_id'] is not None:
        if clients[userName]['role'] is not None:
            emit('game_message', {'client': clients[userName]['client_id'],
                                  'message': '游戏已经开始，重新连接成功'},
                 broadcast=False, room=clients[userName]['client_id'])

            emit('game_message', {'client': None, 'message': '============='},
                 broadcast=False, room=clients[userName]['client_id'])

            emit('game_message', {'client': clients[userName]['client_id'],
                                  'message': f'{smartPlayer}是大聪明'},
                 broadcast=False, room=clients[userName]['client_id'])

            emit('game_message', {'client': clients[userName]['client_id'],
                                  'message': f'\n词语： {word["word"]}\n '
                                             f'难度： {word["difficulty"]}\n '
                                             f'提示： {word["hint"]}'},
                 broadcast=False, room=clients[userName]['client_id'])

            if clients[userName]['role'] == 'liar':
                message = '【你是瞎掰人】：请准备瞎掰！'
            elif clients[userName]['role'] == 'honest':
                message = '【你是老实人】：故事：\n' + word['story']
            else:
                message = '【你是大聪明】：给出一个倒计时信号！'
            emit('game_message', {'client': clients[userName]['client_id'],
                                  'message': message},
                 broadcast=False, room=clients[userName]['client_id'])


def join_after_start(userName):
    if startGame and clients[userName]['client_id'] is not None:
        emit('system_message', {'client': clients[userName]['client_id'],
                                'message': '游戏已经开始，请等待本轮游戏结束'},
             broadcast=False, room=clients[userName]['client_id'])


if __name__ == '__main__':
    socketio.run(app, port=5002)
