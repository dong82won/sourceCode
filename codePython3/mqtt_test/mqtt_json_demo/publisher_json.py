import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
import json  # 💡 JSON 라이브러리 추가

broker_address = "localhost"

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.connect(broker_address, 1883, 60)

try:
    count = 0
    while True:
        count += 1
        
        # 💡 보낼 데이터를 딕셔너리 형태로 구조화
        sensor_data = {
            "device_id": "notebook_A",
            "count": count,
            "temperature": 25.4 + (count * 0.1),
            "status": "OK"
        }
        
        # 💡 딕셔너리를 JSON 문자열로 변환 (Serialization)
        json_message = json.dumps(sensor_data)

        client.publish("test/topic", json_message)
        print(f"발행 완료(JSON): {json_message}")
        time.sleep(2)
except KeyboardInterrupt:
    client.disconnect()