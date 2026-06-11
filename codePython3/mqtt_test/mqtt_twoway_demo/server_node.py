import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json

broker_address = "localhost"
sub_topic = "greenhouse/sensor/telemetry"
pub_topic = "greenhouse/actuator/command"

# 1. 온실로부터 센서 데이터를 수신했을 때 실행되는 콜백 함수
def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        sensor_data = json.loads(payload_str)
        
        temperature = sensor_data['temperature']
        print(f"📥 [서버 수신] {sensor_data['device_id']} 측측 온도: {temperature}°C")
        
        # 💡 양방향 알고리즘 제어 핵심 조건식
        # 온도가 26.0도 이상으로 과열되면 장비 제어 명령을 역으로 발송(Publish)합니다.
        if temperature >= 26.0:
            print(f"🚨 [위험 감지] 온도가 {temperature}°C 로 너무 높습니다! 에어컨 가동 명령을 보냅니다.")
            
            command_payload = {
                "target": "air_conditioner",
                "action": "ON"
            }
            
            # 제어 토픽으로 명령 발송
            client.publish(pub_topic, json.dumps(command_payload))
            
    except Exception as e:
        print(f"⚠️ 데이터 처리 에러: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ 관제 서버: 브로커 연결 성공!")
        client.subscribe(sub_topic)
        print(f"📡 센서 데이터 수신 채널('{sub_topic}') 모니터링 시작.")
    else:
        print(f"❌ 연결 실패: {rc}")

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)

# 서버는 데이터 수신에만 집중하면 되므로 loop_forever()로 대기합니다.
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n서버 관제를 종료합니다.")
    client.disconnect()