from socket import *
import time
import os

print("**************************************************************************")
print("  _____                   _____                  _____ _ _            _   ")
print(" |  __ \                 / ____|                / ____| (_)          | |  ")
print(" | |  | | ___  ___ _ __ | |     _ __ ___  _ __ | |    | |_  ___ _ __ | |_ ")
print(" | |  | |/ _ \/ _ \ '_ \| |    | '__/ _ \| '_ \| |    | | |/ _ \ '_ \| __|")
print(" | |__| |  __/  __/ |_) | |____| | | (_) | |_) | |____| | |  __/ | | | |_ ")
print(" |_____/ \___|\___| .__/ \_____|_|  \___/| .__/ \_____|_|_|\___|_| |_|\__|")
print("                  | |                    | |                              ")
print("                  |_|                    |_|                              ")
print("**************************************************************************")
print("* host : ", end='')

host = input()
port = 7890

client = socket(AF_INET, SOCK_STREAM)
client.connect((host, port))
print('* AI 서버와 연결되었습니다.')

images_dir = './images'
images = [file for file in os.listdir(images_dir) if file.endswith('.png')]

idx = 0
for image_name in images:
    idx += 1
    image_path = images_dir + '/' + image_name
    remain_size = image_size = os.path.getsize(image_path)

    if idx < 10:
        print(f"* 이미지 ({image_name}:{round(image_size / 1024, 2)}KB)를 성공적으로 송신하였습니다.")
        continue

    client.send("0".encode('utf-8').ljust(64)) # operation
    result = int(client.recv(64).decode('utf-8'))

    if result < 0:
        error_message = client.recvall(1024).decode('utf-8')
        print(f"* 이미지 ({image_name}) 송신을 실패하였습니다. : {error_message}")
        continue

    client.send(str(len(image_name)).encode('utf-8').ljust(64))
    client.send(image_name.encode('utf-8'))
    client.send(str(image_size).encode('utf-8').ljust(64))
    
    # 이미지 파일 송신
    with open(image_path, 'rb') as f:
        try:
            while remain_size > 0:
                send_size = 1024
                remain_size -= send_size

                if remain_size < 0:
                    send_size += remain_size
                    remain_size = 0

                data = f.read(send_size)
                client.send(data)

            f.close()
        except Exception as e:
            print(f"* 이미지 ({image_name}) 송신을 실패하였습니다.")
            print(e)

    # 서버 처리 결과 수신
    result = int(client.recv(64).decode('utf-8'))
    if result < 0:
        error_message = client.recvall(1024).decode('utf-8')
        print(f"* 이미지 ({image_name}) 송신을 실패하였습니다. : {error_message}")
    else:
        print(f"* 이미지 ({image_name}:{round(image_size / 1024, 2)}KB)를 성공적으로 송신하였습니다.")

    time.sleep(30)
    
# 끝
client.close()