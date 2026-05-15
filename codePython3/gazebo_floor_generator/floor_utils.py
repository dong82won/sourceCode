import os
import math

def parse_wall_data(link):
    """SDF link 엘리먼트에서 벽 데이터를 추출하고 반시계 방향으로 90도 회전합니다."""
    try:
        p = list(map(float, link.find('pose').text.split()))
        s = list(map(float, link.find('.//box/size').text.split()))
        # 높이가 0.5 미만인 것은 벽이 아닌 바닥이나 기타 객체로 간주하고 무시
        if s[2] < 0.5: return None

        # 기존 yaw 값에 따른 w, h 계산
        yaw = abs(math.degrees(p[5])) % 180
        w, h = (s[1], s[0]) if 80 < yaw < 100 else (s[0], s[1])

        return {'px': p[0], 'py': p[1], 'w': w, 'h': h}

    except Exception as e:
        # 에러 발생 시 None 반환하여 해당 링크 건너뜀
        return None


def subtract_rect(r1, r2):
    """사각형 r1에서 r2와 겹치는 부분을 제외한 나머지 영역들을 반환합니다."""
    ix1, iy1, ix2, iy2 = max(r1[0], r2[0]), max(r1[1], r2[1]), min(r1[2], r2[2]), min(r1[3], r2[3])
    if ix1 >= ix2 or iy1 >= iy2: return [r1]
    res = []
    if r1[0] < ix1: res.append((r1[0], r1[1], ix1, r1[3]))
    if ix2 < r1[2]: res.append((ix2, r1[1], r1[2], r1[3]))
    if r1[1] < iy1: res.append((ix1, r1[1], ix2, iy1))
    if iy2 < r1[3]: res.append((ix1, iy2, ix2, r1[3]))
    return res

def create_material_script(scripts_path, mat_name, base_material_name):
    """
    제공된 템플릿을 사용하여 개별 .material 스크립트 파일을 생성합니다.
    """
    mat_file_name = f"{mat_name}.material"
    content = f"""material {mat_name}
{{
  technique
  {{
    pass
    {{
      ambient 1 1 1 1.000000
      diffuse 1 1 1 1.000000
      specular 0.03 0.03 0.03 1.000000

      texture_unit
      {{
        texture {base_material_name}
      }}
    }}
  }}
}}
"""
    with open(os.path.join(scripts_path, mat_file_name), 'w', encoding='utf-8') as f:
        f.write(content)