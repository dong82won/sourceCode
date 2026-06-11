import cv2
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time

# 테스트 환경에 맞게 브로커 주소 설정 ('localhost' 또는 실제 노트북 A의 IP)
broker_address = "localhost"
topic = "device/camera/snapshot"

# MQTT 클라이언트 초기화
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

print("🚀 브로커에 연결 중...")
client.connect(broker_address, 1883, 60)

# 0번 내장 웹캠을 활성화 (웹캠이 없다면 아래 주석 코드처럼 이미지 파일을 읽으셔도 됩니다)
cap = cv2.VideoCapture(6)

if not cap.isOpened():
    print("⚠️ 카메라를 열 수 없습니다. 카메라 연결을 확인하거나 이미지 파일 모드로 전환하세요.")
    # 대체용 코드: frame = cv2.imread("test.jpg")

print("📸 스냅샷 전송 시작 (3초 간격, 종료하려면 Ctrl + C)...")

try:
    count = 0
    while True:
        # 카메라로부터 프레임 한 장 읽기
        ret, frame = cap.read()
        if not ret:
            print("⚠️ 프레임을 가져오지 못했습니다.")
            time.sleep(1)
            continue

        count += 1
        
        # 💡 핵심: 용량을 줄이고 전송 속도를 높이기 위해 이미지를 JPG 포맷으로 압축
        # [cv2.IMWRITE_JPEG_QUALITY, 80] 은 화질을 80% 수준으로 압축하여 용량을 최적화합니다.
        ret_encode, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        if ret_encode:
            # 💡 압축된 JPG 이미지를 MQTT가 보낼 수 있는 바이너리(Bytes) 배열로 변환
            jpg_as_bytes = buffer.tobytes()
            
            # 용량 확인 크기 출력 (보통 수십~수백 KB 내외로 압축됩니다)
            print(f"[{count}] 스냅샷 압축 완료 - 크기: {len(jpg_as_bytes) / 1024:.2f} KB")
            
            # MQTT 브로커로 바이너리 데이터 직접 전송
            client.publish(topic, jpg_as_bytes, qos=0)
            print(f"✅ 토픽 '{topic}'으로 전송 완료.")
        
        # 3초 대기 (원하는 초 단위로 변경 가능)
        time.sleep(3)

except KeyboardInterrupt:
    print("\n정지 신호 감지. 프로그램을 안전하게 종료합니다.")
finally:
    # 자원 해제
    cap.release()
    client.disconnect()