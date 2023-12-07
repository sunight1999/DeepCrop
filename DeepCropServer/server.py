from datetime import datetime
from defines import *
from socket import *
import select
import threading
import time
import os
import shutil

print("*******************************************************************************")
print("  _____                   _____                 _____                          ")
print(" |  __ \                 / ____|               / ____|                         ")
print(" | |  | | ___  ___ _ __ | |     _ __ ___  _ __| (___   ___ _ ____   _____ _ __ ")
print(" | |  | |/ _ \/ _ \ '_ \| |    | '__/ _ \| '_ \\___ \ / _ \ '__\ \ / / _ \ '__|")
print(" | |__| |  __/  __/ |_) | |____| | | (_) | |_) |___) |  __/ |   \ V /  __/ |   ")
print(" |_____/ \___|\___| .__/ \_____|_|  \___/| .__/_____/ \___|_|    \_/ \___|_|   ")
print("                  | |                    | |                                   ")
print("                  |_|                    |_|                                   ")
print("*******************************************************************************")
print("* host : ", end='')

host = input()
port = 7890
images_dir = './images'

# 서버 초기 설정
server = socket(AF_INET, SOCK_STREAM)
server.bind((host, port))
server.listen(1)
print(f'* 서버가 {host}:{port}에서 대기 중입니다...')

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
    sock.sendall(str(res).encode('utf-8').ljust(64))

    # 오류가 발생한 경우 오류 메시지 전송
    if res < 0:
        sock.sendall(getError(res))

def saveImage(sock):
    image_name_len = int(sock.recv(64).decode('utf-8'))
    image_name = sock.recv(image_name_len).decode('utf-8')
    remain_size = image_size = int(sock.recv(64).decode('utf-8'))

    with open(f'{images_dir}/{image_name}', 'wb') as f:
        try:
            while remain_size > 0:
                req_size = 1024
                remain_size -= req_size

                # 남은 데이터가 1024보다 작은 경우
                if remain_size < 0:
                    req_size += remain_size + 1
                    remain_size = 0

                data = sock.recv(req_size)
                f.write(data)

            f.close()
        except Exception as e:
            print(f'* 이미지 ({image_name}) 수신을 실패하였습니다. :')
            print(e)
            
    print(f"* 이미지 ({image_name}:{round(image_size / 1024, 2)}KB)를 성공적으로 수신하였습니다.")
    image_queue.append(image_name)

def monitorImageQueue():
    while True:
        # 이미지 큐에 새로운 작물 이미지가 들어왔는지 모니터링
        while len(image_queue) > 0:
            image = image_queue.pop()

            # 이미지가 들어왔다면 수확량 예측 수행
            predict = predictImage(image)

            # 예측값을 유니티에 전달
            for sock in unity_socks:
                now = str(datetime.now())
                sock.send(str(len(now)).encode('utf-8').ljust(64))
                sock.send(str(datetime.now()).encode('utf-8'))
                sock.send(str(predict).encode('utf-8').ljust(64))
        
        time.sleep(IMAGE_QUEUE_MONITORING_DELAY)

def predictImage(image):
    src = f'./images/{image}'
    dest = f'/share/test/1-58/tomato/images/{image}'
    shutil.copyfile(src, dest)
    
    # 예측 수행
    result = os.system('./pred-tomato.sh')
    if result != 0:
        print(f'예측 쉘 스크립트 수행을 실패하였습니다.({result})')
        return -1

    # 이미지 파일 제거
    #os.remove(src)
    os.remove(dest)

    # 결과 추출
    predict = 0
    with open(f'./runs/val/exp2/labels/{image.split(".")[0]}.txt') as f:
        lines = f.readlines()
        predict = len(lines)

    # 다음 분석을 위해 결과 폴더 제거
    shutil.rmtree('./runs/val')

    return predict

def removeClinet(sock):
    if sock in read_socks:
        read_socks.remove(sock)

    if sock in unity_socks:
        unity_socks.remove(sock)

    print(f'* 클라이언트 ({sock})의 연결을 해제하였습니다.')

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
            print(f"* {addr}에서 연결하였습니다.")

            read_socks.append(client)
        # 연결된 클라이언트 통신 처리
        else:
            try:
                data = sock.recv(64).decode('utf-8')
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
                continue

            # op 0 : 라즈베리파이 -> AI Sever 이미지 전송
            if operation == 0:
                print('op is zero')
                saveImage(sock)
                result(sock, SUCCESS)
            # op 1 : 유니티 클라이언트 리스너 등록
            elif operation == 1:
                unity_socks.append(sock)
                read_socks.remove(sock)
            # op ? : 알 수 없는 operation 처리
            else:
                result(sock, INVALID_OPERATION)
    