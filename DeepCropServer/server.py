from datetime import datetime
from defines import *
from socket import *
import select
import threading
import time

host = "127.0.0.1"
port = 7890

# 서버 초기 설정
server = socket(AF_INET, SOCK_STREAM)
server.bind((host, port))
server.listen(1)
print(f'서버가 {host}:{port}에서 대기 중입니다...')

read_socks = [server]
unity_socks = []

image_queue = []

# Helper Functions
def getError(res):
    message = ''

    if res == INVALID_VALUE_TYPE:
        message = '잘못된 데이터 타입입니다.'
    elif res == INVALID_OPERATION:
        message = '잘못된 operation입니다.'
    elif res == UNIMPLEMENTED_OPERATION:
        message = '구현되지 않은 operation입니다.'
    else:
        message = '알 수 없는 오류가 발생하였습니다.'

    return message.encode('utf-8')
    
def result(sock, res):
    sock.sendall(str(res).encode('utf-8'))

    # 오류가 발생한 경우 오류 메시지 전송
    if res < 0:
        sock.sendall(getError(res))

def monitorImageQueue():
    while True:
        # 이미지 큐에 새로운 작물 이미지가 들어왔는지 모니터링
        while len(image_queue) > 0:
            image = image_queue.pop()

            # 이미지가 들어왔다면 수확량 예측 수행
            predict = predictImage(image)

            # 예측값을 유니티에 전달
            for sock in unity_socks:
                sock.sendall(str(datetime.now()).encode('utf-8'))
                sock.sendall(str(predict).encode('utf-8'))
        
        time.sleep(IMAGE_QUEUE_MONITORING_DELAY)

pre = 1
def predictImage(image):
    global pre
    pre += 1

    if pre == 3:
        pre = 1

    return pre

def removeClinet(sock):
    if sock in read_socks:
        read_socks.remove(sock)

    if sock in unity_socks:
        unity_socks.remove(sock)

    print(f'클라이언트 ({sock})의 연결을 해제하였습니다.')

# 이미지 큐 모니터링 시작
image_queue_monitor = threading.Thread(target = monitorImageQueue)
image_queue_monitor.start()

# 서버 select 및 accept 시작
while True:
    readables, writeables, exceptions = select.select(read_socks, [], [])

    for sock in readables:
        # 신규 클라이언트가 접속한 경우
        if sock == server:
            client, addr = server.accept()
            print(f"{addr}에서 연결하였습니다.")

            read_socks.append(client)
        # 연결된 클라이언트 통신 처리
        else:
            try:
                data = sock.recv(1024).decode('utf-8')
            except ConnectionResetError as e:
                removeClinet(sock)
                continue
                
            # 클라이언트가 종료된 경우 처리
            if not data:
                removeClinet(sock)
                continue

            # operation 받기
            try:
                operation = int(data)
                result(sock, SUCCESS)
            except ValueError:
                result(sock, INVALID_VALUE_TYPE)

            # op 0 : 라즈베리파이 -> AI Sever 이미지 전송
            if operation == 0:
                print('op is zero')
                image_queue.append(0)
                result(sock, SUCCESS)
            # op 1 : 유니티 클라이언트 리스너 등록
            elif operation == 1:
                unity_socks.append(sock)
                read_socks.remove(sock)
                result(sock, SUCCESS)
            # op ? : 알 수 없는 operation 처리
            else:
                result(sock, INVALID_OPERATION)
    