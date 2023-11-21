from socket import *
import time

host = '127.0.0.1'
port = 7890

client = socket(AF_INET, SOCK_STREAM)
client.connect((host, port))
print('AI 서버와 연결되었습니다.')

# 임시 데이터 1차 전송
client.send('0'.encode('utf-8'))
time.sleep(10)

# 임시 데이터 2차 전송
client.send('0'.encode('utf-8'))
time.sleep(1)

# 끝
client.close()