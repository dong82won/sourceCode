import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json

broker_address = "localhost"

# 💡 1. 브로커에 연결 성공했을 때 실행될 콜백 함수 추가
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ 브로커 연결 성공!")
        # 💡 여기가 중요합니다! 연결이 성공하면 토픽을 구독합니다.
        client.subscribe("test/topic")
        print("📡 주제('test/topic') 구독 시작... 메시지를 기다리는 중입니다.")
    else:
        print(f"❌ 연결 실패, 결과 코드: {rc}")

# 2. 메시지가 도착했을 때 실행되는 콜백 함수
def on_message(client, userdata, msg):
    try:
        # 수신된 바이트 데이터를 문자열로 디코딩
        payload_str = msg.payload.decode('utf-8')
        # JSON 문자열을 파이썬 딕셔너리로 변환
        data = json.loads(payload_str)
        print(f"📦 수신 완료! 기기명: {data['device_id']}, 온도는: {data['temperature']}°C")
    except Exception as e:
        print(f"⚠️ 데이터 파싱 에러: {e}")

# 클라이언트 생성
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

# 💡 3. 새로 만든 on_connect 콜백 함수 등록
client.on_connect = on_connect
client.on_message = on_message

print(f"노트북 브로커({broker_address})에 연결 시도 중...")
client.connect(broker_address, 1883, 60)

# 무한 루프 시작
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("구독을 종료합니다.")
    client.disconnect()