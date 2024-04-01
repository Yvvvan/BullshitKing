import socket
import threading
import random

# 创建TCP Socket, 类型为服务器之间网络通信，流式Socket
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 绑定服务器端的IP和端口
mySocket.bind(('127.0.0.1', 5001))
# 开始监听TCP传入连接，并设置操作系统可以挂起的最大连接数量
mySocket.listen(5)

print('Server was started by ', socket.gethostbyname('localhost'), 'now is listening ...')
# 创建字典，用于存储客户端的用户
mydict = dict()
# 创建列表，用于存储客户端的连接
# mylist = list()

assignRole = False
smartPlayer = None
honestPlayer = None
startGame = False
playerLimit = 4
playerListUpdated = False
selectedWord = None

wordDataBase = [
    {'word': '模拟词语',
     'difficulty': 1,
     'hint': '提示/词语/啊',
     'store': '模拟词语是我在做这个游戏的时候用来模拟的词语。',
     },
]


# 把聊天信息发送给除自己以外的所有人
def chatMsgToOthers(exceptMe, chatMsg):
    for c in mydict:
        if c != exceptMe:
            try:
                # 向客户端发送消息
                mydict[c]['connection'].send(chatMsg.encode())
            except:
                pass


def searchSender(connNum):
    for i in mydict:
        # 如果有 connection
        if mydict[i]['connection'] is not None:
            if mydict[i]['connection'].fileno() == connNum:
                return i


def numberPlayers(playerdict):
    count = 0
    for i in playerdict:
        if playerdict[i]['connection'] is not None:
            count += 1
    return count


# 保持与客户端连接的子线程的处理逻辑
def subThreadProcess(myconnection, connNum):
    global assignRole, smartPlayer, honestPlayer, startGame, playerLimit, playerListUpdated, selectedWord
    # 接收客户端消息
    username = myconnection.recv(1024).decode()
    if username not in mydict:
        newuser = True
    else:
        newuser = True
        # 如果username已存在在mydict中，提示用户重新输入
        while username in mydict:
            # 如果这个用户名的连接还存在（用户名被占用），提示用户重新输入
            if mydict[username]['connection'] is not None:
                myconnection.send('【系统提示】：此昵称已经存在，请重新输入'.encode())
                username = myconnection.recv(1024).decode()
            # 如果这个用户名的连接已经关闭（用户名曾经被使用），则ok
            else:
                newuser = False
                mydict[username]['connection'] = myconnection
                break
    if newuser:
        mydict[username] = {
            'username': username,
            'connection': myconnection,
            'currentrole': None,
        }

    print('client connection number:', connNum, ' has nickname:', username)
    chatMsgToOthers(connNum, '【系统提示】：' + username + '已经进入聊天室，请文明聊天')

    # 如果游戏已经开始，并且玩家角色不是空，发送一次信息给玩家
    if startGame and mydict[username]['currentrole'] is not None:
        if mydict[username]['currentrole'] is not None:
            myconnection.send('游戏已经开始，重新连接成功\n'.encode())
            myconnection.send(('大聪明是：' + smartPlayer + '\n').encode())
            myconnection.send(('【系统提示】：'
                              + '\n词语：' + selectedWord['word']
                              + '\n词语难度：' + str(selectedWord['difficulty'])
                              + '\n词语提示：' + selectedWord['hint']
                              + '\n=====================').encode())
            if mydict[username]['currentrole'] == 'liar':
                myconnection.send('【瞎掰人专属】：请开始瞎编\n'.encode())
            elif mydict[username]['currentrole'] == 'honest':
                myconnection.send(('【老实人专属】：' + '故事：' + selectedWord['store']).encode())

    while True:
        # 分配角色
        if numberPlayers(mydict) > playerLimit - 1 and not assignRole and startGame:
            assignRole = True
            # 从mydict中随机选择一个key
            player_1 = random.choice(list(mydict.keys()))  # 大聪明
            player_2 = player_1  # 老实人
            while player_1 == player_2:
                player_2 = random.choice(list(mydict.keys()))
            smartPlayer = player_1
            honestPlayer = player_2
            # 这个player是“大聪明” 其他人是“瞎掰人”
            for i in mydict:
                if mydict[i]['connection'] is not None:
                    if i == player_1:
                        mydict[i]['connection'].send('你是大聪明'.encode())
                        mydict[i]['currentrole'] = 'smart'
                    elif i == player_2:
                        mydict[i]['connection'].send('你是老实人'.encode())
                        mydict[i]['currentrole'] = 'honest'
                    else:
                        mydict[i]['connection'].send('你是瞎掰人'.encode())
                        mydict[i]['currentrole'] = 'liar'

            # 把大聪明的名字发给所有人
            chatMsgToOthers(-1, '【系统提示】：' + player_1 + '是大聪明!')

            # 在wordDataBase中随机选择一个词语，把词语发给所有人
            word = random.choice(wordDataBase)
            selectedWord = word

            chatMsgToOthers(-1, '【系统提示】：'
                            + '\n词语：' + word['word']
                            + '\n词语难度：' + str(word['difficulty'])
                            + '\n词语提示：' + word['hint']
                            + '\n=====================')

            # 把词语的store发给老实人，把“开编”发送给瞎掰人
            for i in mydict:
                if mydict[i]['connection'] is not None:
                    if i == player_1:
                        mydict[i]['connection'].send('【大聪明专属】：请开始一个倒计时！'.encode())
                    elif i == player_2:
                        mydict[i]['connection'].send(('【老实人专属】：' + '故事：' + word['store']).encode())
                    else:
                        mydict[i]['connection'].send('【瞎掰人专属】：请开始瞎编'.encode())

            print('大聪明是：', player_1)
            print('老实人是：', player_2)
            print('词语是：', word['word'], '，提示是：', word['hint'], '，故事是：', word['store'], '，难度是：', word['difficulty'])

        # 检查是否满足游戏开始的条件
        if numberPlayers(mydict) > playerLimit - 1 and not startGame and playerListUpdated:
            playerListUpdated = False
            chatMsgToOthers(-1, '【系统提示】：游戏人数已满足，请任意玩家输入“start”开始游戏，也可以继续等待更多玩家加入')

        # 游戏结束

        # 聊天系统
        try:
            # 接收客户端消息
            recvedMsg = myconnection.recv(1024).decode()
            sender = searchSender(connNum)
            if recvedMsg:
                print(sender, ': ', recvedMsg)
                chatMsgToOthers(sender, sender + ': ' + recvedMsg)

            if recvedMsg == 'start' and not startGame and numberPlayers(mydict) > playerLimit - 1:
                startGame = True
                connection.send(b'game start')

            if recvedMsg == 'end' and startGame:
                startGame = False
                assignRole = False
                playerListUpdated = True
                chatMsgToOthers(-1, '【系统提示】：游戏结束，大家辛苦了！')
                for i in mydict:
                    mydict[i]['currentrole'] = None

        except (OSError, ConnectionResetError):
            sender = searchSender(connNum)
            mydict[sender]['connection'] = None
            print(sender, 'was exit, ', numberPlayers(mydict), ' person left!')
            chatMsgToOthers(connNum, '【系统提示】：' + sender + ' 已经离开')
            myconnection.close()
            return


# 开始连接
while True:
    # 接受TCP连接并返回（connection,address）,其中connection是新的Socket对象，可以用来接收和发送数据,address是连接客户端的地址。
    connection, address = mySocket.accept()
    print('Accept a new connection', connection.getsockname(), connection.fileno())
    try:
        # 接收客户端消息
        buf = connection.recv(1024).decode()
        if buf == 'hello':
            # 向客户端发送消息
            connection.send(b'connection success, welcome to chat room!')
            playerListUpdated = True
            # 为当前连接创建一个新的子线程来保持通信
            myThread = threading.Thread(target=subThreadProcess, args=(connection, connection.fileno()))
            myThread.daemon = True
            myThread.start()
        else:
            # 向客户端发送消息
            connection.send(b'connection fail, please go out!')
            connection.close()
    except:
        pass
