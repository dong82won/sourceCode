import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
import json

broker_address = "localhost"
pub_topic = "greenhouse/sensor/telemetry"
sub_topic = "greenhouse/actuator/command"

# 💡 온도를 전역 변수로 선언하여 언제든 초기화할 수 있도록 합니다.
current_temp = 22.0

# 1. 서버로부터 제어 명령(Command)을 받았을 때 실행되는 콜백 함수
def on_message(client, userdata, msg):
    global current_temp # 💡 전역 변수인 온도를 제어하겠다고 선언
    
    try:
        payload_str = msg.payload.decode('utf-8')
        command_data = json.loads(payload_str)
        
        print("\n========================================")
        print(f"🤖 [서버 명령 수신] 제어 대상: {command_data['target']}")
        print(f"⚙️ [장치 상태 변경] 에어컨 전원 제어: {command_data['action']}")
        
        # 💡 핵심: 서버에서 에어컨 ON 명령이 오면 온도를 즉시 20.0도로 초기화합니다!
        if command_data['action'] == "ON":
            print("❄️ [에어컨 가동] 내부 온도를 20.0°C로 초기화(냉각)합니다.")
            current_temp = 20.0
            
        print("========================================")
        
    except Exception as e:
        print(f"⚠️ 명령 파싱 에러: {e}")

# 2. 브로커에 연결되었을 때 서버의 명령 채널을 구독
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
client.loop_start()

try:
    count = 0
    while True:
        count += 1
        # 2초마다 온도가 0.5도씩 상승
        current_temp += 0.5 
        
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
    client.loop_stop()
    client.disconnect()