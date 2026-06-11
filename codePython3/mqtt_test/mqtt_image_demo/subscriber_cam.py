import cv2
import numpy as np
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

broker_address = "localhost"
topic = "device/camera/snapshot"

# 브로커 연결 성공 시 콜백
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ MQTT 브로커 연결 성공!")
        client.subscribe(topic)
        print(f"📡 '{topic}' 구독 시작... 이미지 패킷을 대기합니다.")
    else:
        print(f"❌ 연결 실패, 결과 코드: {rc}")

# 메시지 수신 시 콜백
def on_message(client, userdata, msg):
    try:
        # 1. 수신된 msg.payload(바이트 데이터)를 넘파이(Numpy) 1차원 배열로 변환
        np_array = np.frombuffer(msg.payload, dtype=np.uint8)

        # 2. 넘파이 배열을 압축 해제하여 OpenCV 이미지 객체로 디코딩
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is not None:
            print(f"📦 스냅샷 수신 성공! 화면에 표시합니다. (패킷 크기: {len(msg.payload)/1024:.2f} KB)")            
            # 3. 우분투 GUI 창에 이미지 띄우기
            cv2.imshow("MQTT Live Snapshot", image)
            # GUI 윈도우 창이 갱신되고 이벤트를 처리할 시간을 주기 위해 최소 1ms 대기
            cv2.waitKey(1)
        else:
            print("⚠️ 수신된 데이터를 이미지로 변환하는 데 실패했습니다.")
    except Exception as e:
        print(f"⚠️ 이미지 복원 중 에러 발생: {e}")

# 클라이언트 설정 및 콜백 등록
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print(f"노트북 브로커({broker_address})에 접속 시도 중...")
client.connect(broker_address, 1883, 60)

# 무한 루프로 메시지 지속 수신
try:
    client.loop_forever()

except KeyboardInterrupt:
    print("\n구독을 종료합니다.")

finally:
    # 프로그램 종료 시 켜져 있던 OpenCV 창들을 모두 깔끔하게 닫아줍니다.
    cv2.destroyAllWindows()
    client.disconnect()