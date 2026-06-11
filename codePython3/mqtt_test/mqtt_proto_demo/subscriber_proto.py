# 우분투 22.04의 컴파일러와 찰떡궁합인 3.20.3 버전
# pip install "protobuf==3.20.3"

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
# import mqtt_proto_demo.data_pb2 as data_pb2  # 💡 컴파일러가 만들어준 파일 임포트
import data_pb2  # 💡 컴파일러가 만들어준 파일 임포트


broker_address = "localhost"

# 1. 브로커에 연결 성공했을 때 실행될 콜백 함수
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ 브로커 연결 성공!")
        # 연결 직후 프로토콜 버퍼 전용 토픽 구독 신청
        client.subscribe("test/protobuf")
        print("📡 주제('test/protobuf') 구독 시작... 메시지 대기 중.")
    else:
        print(f"❌ 연결 실패, 결과 코드: {rc}")

# 2. 메시지가 도착했을 때 실행되는 콜백 함수
def on_message(client, userdata, msg):
    try:
        # 💡 깨진 글자처럼 보이는 바이너리(msg.payload)를 파이썬 객체로 복원 (역직렬화)
        sensor = data_pb2.SensorData()
        sensor.ParseFromString(msg.payload)
        
        # 💡 일반 파이썬 객체처럼 변수 접근 가능
        print("-" * 50)
        print(f"📦 [Protobuf 데이터 수신 장치: {sensor.device_id}]")
        print(f"   카운트: {sensor.count}")
        print(f"   현재 온도: {sensor.temperature:.2f}°C")
        print(f"   장치 상태: {sensor.status}")
        
    except Exception as e:
        print(f"⚠️ 데이터 역직렬화 실패(패킷 오류): {e}")

# 클라이언트 생성
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

# 콜백 함수 세팅
client.on_connect = on_connect
client.on_message = on_message

print(f"노트북 브로커({broker_address})에 연결 시도 중...")
client.connect(broker_address, 1883, 60)

# 메시지 수신 무한 루프 구동
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n구독을 종료합니다.")
    client.disconnect()