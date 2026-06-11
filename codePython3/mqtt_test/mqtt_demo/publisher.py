import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

import time

# 노트북 A 자신의 IP 주소를 적거나, 로컬인 경우 'localhost' 사용 가능
broker_address = "localhost"

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

print("브로커에 연결 중...")
client.connect(broker_address, 1883, 60)

try:
    count = 0
    while True:
        count += 1
        message = f"노트북 A에서 보낸 메시지 #{count}"

        # 'test/topic'이라는 주제로 메시지 발행
        client.publish("test/topic", message)
        print(f"발행 완료: {message}")

        time.sleep(2) # 2초마다 전송
except KeyboardInterrupt:
    print("발행을 종료합니다.")
    client.disconnect()