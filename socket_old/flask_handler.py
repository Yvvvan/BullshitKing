from flask_handler import Response
from flask_handler import Flask
from flask_handler import render_template
from flask_handler import request, abort
import socket
import threading

app = Flask(__name__)

@app.route('/')
def index():
    # 假设有一些数据
    user = {'username': 'John', 'email': 'john@example.com'}
    posts = [
        {'author': 'John', 'title': 'First post', 'content': 'Hello, world!'},
        {'author': 'Jane', 'title': 'Second post', 'content': 'Another day, another dollar.'}
    ]
    # 渲染模板时，可以将数据作为关键字参数传递给 render_template 函数
    return render_template('index.html', title='Home', user=user, posts=posts)


@app.route('/submit', methods=['POST'])
def submit():
    # 从表单中获取输入的文本
    input_text = request.form['input_text']
    try:
        sock.send(input_text.encode())
    except ConnectionAbortedError:
        print('Server closed this connection!')
        exit(1)
    except ConnectionResetError:
        print('Server is closed!')
        exit(1)
    # 在终端中打印输入的文本
    print("Input Text:", input_text)
    # 可以进行其他处理，比如保存到数据库或返回给客户端
    return '', 204



# 向服务器端发送消息的处理逻辑
def sendThreadProcess():
    while True:
        try:
            myMsg = input('me: ')
            sock.send(myMsg.encode())
        except ConnectionAbortedError:
            print('Server closed this connection!')
            exit(1)
        except ConnectionResetError:
            print('Server is closed!')
            exit(1)

# 向服务器端接收消息的处理逻辑
def recvThreadProcess():
    while True:
        try:
            otherMsg = sock.recv(1024)
            if otherMsg:
                print('\n' + otherMsg.decode())
            else:
                pass
        except ConnectionAbortedError:
            print('Server closed this connection!')
            exit(1)
        except ConnectionResetError:
            print('Server is closed!')
            exit(1)

if __name__ == '__main__':
    # 创建TCP Socket, 类型为服务器之间网络通信，流式Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 通过IP和端口号连接服务器端Socket, 类型为服务器之间网络通信，流式Socket
    sock.connect(('127.0.0.1', 50000))
    # 向服务器发送连接请求
    sock.send(b'hello')
    # 从服务器接收到的消息
    print(sock.recv(1024).decode())
    # username = input('请输入你的昵称: ')
    # # 向服务器发送聊天用户名H
    # sock.send(username.encode())

    # 创建发送和接收消息的子线程
    # sendThread = threading.Thread(target=sendThreadProcess)
    recvThread = threading.Thread(target=recvThreadProcess)
    threads = [recvThread]

    for t in threads:
        t.daemon = True
        t.start()

    app.run(port=15320, debug=True,
            threaded=True, use_reloader=False)