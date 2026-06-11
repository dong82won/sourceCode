import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# ⚠️ 중요: 노트북 A의 IP 주소를 입력하세요! (예: "192.168.0.15")
# 같은 노트북 안에서 테스트할 때는 'localhost'를 적어줍니다.
broker_address = "localhost"

# 브로커와 연결이 성공했을 때 실행되는 콜백 함수
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("브로커 연결 성공!")
        # 연결 성공 시 'test/topic' 구독 시작
        client.subscribe("test/topic")
        print("주제('test/topic') 구독 시작...")
    else:
        print(f"연결 실패, 결과 코드: {rc}")

# 메시지가 도착했을 때 실행되는 콜백 함수
def on_message(client, userdata, msg):
    print(f" 수신된 메시지 [{msg.topic}]: {msg.payload.decode('utf-8')}")

# 클라이언트 생성
# client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

# 콜백 함수 등록
client.on_connect = on_connect
client.on_message = on_message

print(f"노트북 A 브로커({broker_address})에 연결 시도 중...")
client.connect(broker_address, 1883, 60)

# 네트워크 루프를 무한 실행하여 메시지를 지속적으로 수신
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("구독을 종료합니다.")
    client.disconnect()