import requests
from datetime import datetime, timedelta

# 지역명 → 격자 좌표 매핑 테이블
REGION_MAP = {
    '서울': (55, 127),
    '부산': (98, 76),
    '대구': (89, 90),
    '인천': (54, 124),
    '광주': (58, 74),
    '대전': (67, 100),
    '울산': (102, 84),
}

def get_current_date_string():
    current_date = datetime.now().date()
    return current_date.strftime("%Y%m%d")

def get_base_datetime():
    """
    현재 시각을 기준으로 정확한 기상청 발표 일자/시각을 계산합니다.
    """
    now = datetime.now()
    
    # 팩트 체크: 밤 12시~오전 2시 사이면, 무조건 '전날' 밤 11시 데이터를 요청해야 함
    if now.hour < 2:
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"
    
    # 그 외의 시간은 오늘 날짜와 가장 최근 발표 시각 매칭
    base_times = [2, 5, 8, 11, 14, 17, 20, 23]
    for t in reversed(base_times):
        if now.hour >= t:
            return now.strftime("%Y%m%d"), f"{t:02d}00"
            
    return now.strftime("%Y%m%d"), "0200" # 안전장치

# def get_base_time_string():
#     # 단기예보 발표 시각: 0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300
#     now = datetime.now()
#     base_times = [2, 5, 8, 11, 14, 17, 20, 23]

#     # 현재 시각보다 작은 발표 시각 중 가장 최근 값 선택
#     base_hour = None
#     for t in reversed(base_times):
#         if now.hour >= t:
#             base_hour = t
#             break
    
#     if now.hour < 2:
#         yesterday = now - timedelta(days=1)
#         return yesterday.strftime("%Y%m%d"), "2300"

#     # 자정~02시 사이면 전날 2300으로 설정
#     # if base_hour is None:
#     #     base_hour = 23

#     return f"{base_hour:02d}00"

keys = '8cbc4c17cc96624fbbba8d4564f02a00da9cdf685d90eb4c42a4afe678eedc34'
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'



def forecast(region_name: str):
    # 지역명 유효성 검사
    if region_name not in REGION_MAP:
        raise ValueError(f"지원하지 않는 지역입니다: {region_name}\n지원 지역: {list(REGION_MAP.keys())}")

    nx, ny = REGION_MAP[region_name]
    base_date_val, base_time_val = get_base_datetime()
    params = {
        'serviceKey' : keys,
        'pageNo' : '1',
        'numOfRows' : '1000',
        'dataType' : 'JSON',
        'base_date' : base_date_val,
        'base_time' : base_time_val,
        'nx' : nx,
        'ny' : ny
    }

    # 값 요청 (웹 브라우저 서버에서 요청 - url주소와 파라미터)
    res = requests.get(url, params=params)

    # JSON -> 딕셔너리
    dict_data = res.json()

    # 시간별 데이터를 담을 딕셔너리 {fcstDate+fcstTime: {항목: 값}}
    time_map = {}

    for item in dict_data['response']['body']['items']['item']:
        fcst_date = item['fcstDate']
        fcst_time = item['fcstTime']
        category  = item['category']
        value     = item['fcstValue']

        key = fcst_date + fcst_time
        if key not in time_map:
            time_map[key] = {
                'fcst_date': fcst_date,
                'fcst_time': fcst_time,
            }

        # 기온 (단기예보는 TMP 사용)
        if category == 'TMP':
            time_map[key]['tmp'] = value
        # 습도
        elif category == 'REH':
            time_map[key]['hum'] = value
        # 강수확률
        elif category == 'POP':
            time_map[key]['pop'] = value
        # 1시간 강수량
        elif category == 'PCP':
            time_map[key]['pcp'] = value
        # 하늘상태: 맑음(1) 구름많음(3) 흐림(4)
        elif category == 'SKY':
            time_map[key]['sky'] = value

    # 시간 순으로 정렬
    sorted_list = sorted(time_map.values(), key=lambda x: x['fcst_date'] + x['fcst_time'])

    # 현재 시각 이후 데이터만 필터링 후 24시간치 슬라이싱
    now_str = datetime.now().strftime("%Y%m%d%H%M")
    filtered_list = [
        row for row in sorted_list
        if row['fcst_date'] + row['fcst_time'] >= now_str[:11]  # 현재 시각 이후만
    ]
    weather_list = filtered_list[:24]  # 현시간부터 24시간치

    return {
        'region': region_name,
        'data': weather_list  # 시간별 리스트 [{fcst_date, fcst_time, tmp, hum, pop, pcp, sky}, ...]
    }

# 사용자로부터 지역 입력
# region = input(f"지역을 입력하세요 {list(REGION_MAP.keys())}: ")
# result = forecast(region)

# # 결과 확인 출력 (팀원 전달용 raw 데이터)
# print(f"지역: {result['region']}")
# print(f"총 데이터 수: {len(result['data'])}시간치")
# print("--- 24시간 전체 데이터 ---")
# for row in result['data']:
#     print(row)