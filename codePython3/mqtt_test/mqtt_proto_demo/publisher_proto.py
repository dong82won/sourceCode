# 우분투 22.04의 컴파일러와 찰떡궁합인 3.20.3 버전
# pip install "protobuf==3.20.3"

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
#import mqtt_proto_demo.data_pb2 as data_pb2  # 💡 컴파일러가 만들어준 파일 임포트
import data_pb2  # 💡 컴파일러가 만들어준 파일 임포트



# 같은 노트북 안에서 테스트할 때는 'localhost'
broker_address = "localhost"

# 클라이언트 생성 (paho-mqtt 2.x 최신 규격 반영)
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

print("🚀 브로커에 연결 중...")
client.connect(broker_address, 1883, 60)

try:
    count = 0
    while True:
        count += 1

        # 💡 Protobuf 객체 생성 및 데이터 매핑
        sensor = data_pb2.SensorData()
        sensor.device_id = "notebook_A_protobuf"
        sensor.count = count
        sensor.temperature = 26.8 + (count * 0.1)
        sensor.status = "OPERATIONAL"

        # 💡 데이터를 매우 작은 크기의 바이너리(바이트) 스트링으로 변환 (직렬화)
        binary_data = sensor.SerializeToString()

        # 'test/protobuf' 토픽으로 바이너리 데이터 전송
        client.publish("test/protobuf", binary_data)

        print(f"✅ 발행 완료(Protobuf 바이너리 발송) #{count}")
        time.sleep(2)  # 2초 대기

except KeyboardInterrupt:
    print("\n발행을 종료합니다.")
    client.disconnect()