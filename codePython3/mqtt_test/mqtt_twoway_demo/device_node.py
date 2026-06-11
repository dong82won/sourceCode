import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
import json

# 테스트 환경에 맞게 브로커 주소 설정 ('localhost' 또는 상대방 노트북 IP)
broker_address = "localhost"
pub_topic = "greenhouse/sensor/telemetry"
sub_topic = "greenhouse/actuator/command"

# 1. 서버로부터 제어 명령(Command)을 받았을 때 실행되는 콜백 함수
def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        command_data = json.loads(payload_str)
        
        print("\n========================================")
        print(f"🤖 [서버 명령 수신] 제어 대상: {command_data['target']}")
        print(f"⚙️ [장치 상태 변경] 에어컨 전원 제어: {command_data['action']}")
        print("========================================")
        
    except Exception as e:
        print(f"⚠️ 명령 파싱 에러: {e}")

# 2. 브로커에 연결되었을 때 서버의 명령 채널을 구독(Subscribe)
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ 온실 장비: 브로커 연결 성공!")
        client.subscribe(sub_topic)
        print(f"📡 제어 명령 수신 채널('{sub_topic}') 구독 시작.")
    else:
        print(f"❌ 연결 실패: {rc}")

# MQTT 클라이언트 초기화
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)

# 💡 핵심: 백그라운드 스레드에서 수신(on_message) 기능을 독립적으로 시작합니다.
# 이 덕분에 아래 while 루프가 돌면서도 언제든 서버의 메시지를 즉시 받을 수 있습니다.
client.loop_start()

try:
    current_temp = 22.0
    count = 0
    
    while True:
        count += 1
        # 2초마다 온도가 0.5도씩 계속 상승하는 가상 상황 시뮬레이션
        current_temp += 0.5 
        
        # 보낼 센서 데이터 구조화
        sensor_payload = {
            "device_id": "greenhouse_zone_1",
            "temperature": round(current_temp, 2),
            "humidity": 55.4
        }

        json_str = json.dumps(sensor_payload)
        client.publish(pub_topic, json_str)
        print(f"📤 [센서 데이터 발송] 현재 온도: {sensor_payload['temperature']}°C")

        time.sleep(2)

except KeyboardInterrupt:
    print("\n장비 가동을 중단합니다.")
finally:
    client.loop_stop() # 백그라운드 루프 종료
    client.disconnect()