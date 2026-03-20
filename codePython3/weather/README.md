# 날씨 대시보드 (Flet)
<img width="1588" height="1238" alt="image" src="https://github.com/user-attachments/assets/d0a7ecd9-243e-410b-9292-7925a55b2617" />


기상청 단기예보 API를 호출해 **지역별 현재/시간대별 예보**를 보여주는 Flet 데스크톱 앱입니다.

## 기능 소개

- **지역 선택/검색**: 좌측 사이드바에서 지역을 클릭하거나 검색해 조회 ( ** 현재는 서울, 부산, 대구, 인천, 광주, 대전, 울산 의 날씨만 검색, 조회 가능합니다 **)
- **현재 날씨 요약**: 현재 기온, 하늘상태, 습도, 강수확률, 체감온도(근사), 최고/최저
- **Hourly Forecast**: 향후 시간대별 예보(아이콘/기온)
- **배경색 자동 변경**: 하늘상태(맑음/구름많음/흐림)에 따라 배경 그라데이션 변경

## 지원 지역

현재 `src/weather_api.py` 기준 지원 지역은 아래와 같습니다.

- 서울, 부산, 대구, 인천, 광주, 대전, 울산

## 실행 방법

### 1) 환경 준비

- Python **3.10+** 권장

### 2) 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) 실행

```bash
python src/main.py
```

## API 키 주의사항

`src/weather_api.py`의 `keys`(serviceKey)는 **기상청/공공데이터포털 발급 키**가 필요합니다.

- 실행 중 `JSONDecodeError` 등이 발생하면, API 키/호출 제한/응답 오류(HTML 반환 등)일 수 있습니다.
- 필요 시 본인 키로 교체해주세요.

## 프로젝트 구조

- `src/main.py`: Flet UI (대시보드 화면)
- `src/weather_api.py`: 기상청 단기예보 API 호출 및 24시간 데이터 가공
- `src/assets/`: 앱 리소스(아이콘/스플래시)
