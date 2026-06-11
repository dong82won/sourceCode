import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json

broker_address = "localhost"
# 💡 핵심: '+' 와일드카드를 사용하여 어떤 node 이름이 들어오든 전부 낚아챕니다.
sub_topic = "greenhouse/sensor/+"

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        sensor_data = json.loads(payload_str)
        
        target_device = sensor_data['device_id']
        temperature = sensor_data['temperature']
        
        print(f"📥 [서버 수신] 기기명: {target_device} ➡️ 온도: {temperature}°C")
        
        # 💡 특정 디바이스의 온도가 26.0도 이상일 때
        if temperature >= 26.0:
            print(f"🚨 [경고] {target_device} 과열 발생! ({temperature}°C)")
            
            # 💡 중요: 해당 기기의 전용 제어 채널(actuator/기기이름)을 타겟팅하여 명령을 발송합니다.
            specific_pub_topic = f"greenhouse/actuator/{target_device}"
            
            command_payload = {
                "target": "air_conditioner",
                "action": "ON"
            }
            
            client.publish(specific_pub_topic, json.dumps(command_payload))
            print(f"📤 [서버 명령 발송] ➡️ {specific_pub_topic} 채널로 에어컨 가동 명령 전달.")
            
    except Exception as e:
        print(f"⚠️ 서버 데이터 처리 에러: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ 통합 관제 서버: 브로커 연결 성공!")
        client.subscribe(sub_topic)
        print(f"📡 와일드카드 채널('{sub_topic}') 전체 모니터링 시작.")
    else:
        print(f"❌ 연결 실패: {rc}")

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n통합 관제 서버를 종료합니다.")
    client.disconnect()