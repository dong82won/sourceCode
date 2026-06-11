import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
import json
import sys

# 💡 실행할 때 기기 ID를 인자로 받습니다 (예: python3 device_node_multi.py node01)
# 인자를 안 주면 기본값으로 'node_default'를 사용합니다.
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "node_default"

broker_address = "localhost"
pub_topic = f"greenhouse/sensor/{DEVICE_ID}"      # 💡 내 아이디 전용 송신 채널
sub_topic = f"greenhouse/actuator/{DEVICE_ID}"    # 💡 내 아이디 전용 수신 채널

current_temp = 22.0

def on_message(client, userdata, msg):
    global current_temp
    try:
        payload_str = msg.payload.decode('utf-8')
        command_data = json.loads(payload_str)
        
        print(f"\n========================================")
        print(f"🤖 [{DEVICE_ID} 명령 수신] 대상: {command_data['target']}")
        print(f"⚙️ [{DEVICE_ID} 상태 변경] 에어컨: {command_data['action']}")
        
        if command_data['action'] == "ON":
            print(f"❄️ [에어컨 가동] {DEVICE_ID} 내부 온도를 20.0°C로 초기화합니다.")
            current_temp = 20.0
        print(f"========================================")
    except Exception as e:
        print(f"⚠️ 명령 파싱 에러: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ 장비 [{DEVICE_ID}] 브로커 연결 성공!")
        client.subscribe(sub_topic)
        print(f"📡 나를 위한 제어 채널('{sub_topic}') 구독 시작.")
    else:
        print(f"❌ 연결 실패: {rc}")

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)
client.loop_start()

try:
    while True:
        # 💡 각 장비마다 조금씩 다른 온도 상승 패턴을 주기 위해 (시뮬레이션용)
        # node01은 0.5도씩, node02는 0.7도씩 오르도록 설정해보겠습니다.
        increment = 0.7 if "node02" in DEVICE_ID else 0.5
        current_temp += increment
        
        sensor_payload = {
            "device_id": DEVICE_ID,
            "temperature": round(current_temp, 2),
            "humidity": 55.4
        }
        
        client.publish(pub_topic, json.dumps(sensor_payload))
        print(f"📤 [{DEVICE_ID} 데이터 발송] 현재 온도: {sensor_payload['temperature']}°C")
        
        time.sleep(2)

except KeyboardInterrupt:
    print(f"\n장비 [{DEVICE_ID}] 가동을 중단합니다.")
finally:
    client.loop_stop()
    client.disconnect()