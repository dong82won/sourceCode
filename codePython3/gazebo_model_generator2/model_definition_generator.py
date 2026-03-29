import math

def clean_and_offset_pose(pose_str, z_offset=0.0, threshold=0.001):
    """
    1. pose 문자열의 각 수치를 확인하여 임계값(threshold)보다 작으면 0.00000으로 변환합니다.
    2. Z축(인덱스 2)에는 계산된 높이 오프셋을 더해줍니다.
    """
    parts = pose_str.split()
    if len(parts) < 6: return pose_str

    cleaned_parts = []
    for i, val_str in enumerate(parts):
        val = float(val_str)

        # Z축인 경우 오프셋 먼저 적용
        if i == 2:
            val += z_offset

        # 절대값이 임계값(0.001)보다 작으면 0으로 처리
        if abs(val) < threshold:
            cleaned_parts.append("0.00000")
        else:
            # 소수점 5자리까지 표기
            cleaned_parts.append(f"{val:.5f}")
    return " ".join(cleaned_parts)

def calculate_z_offset(pose_str, geo_data):
    """박스의 크기와 회전을 분석하여 수직 높이의 절반(오프셋)을 계산합니다."""
    if not geo_data or geo_data.get("type") != "box":
        return 0.0

    try:
        size = [float(s) for s in geo_data["size"].split()]
        width, depth, height = size # X, Y, Z

        parts = pose_str.split()
        r, p = float(parts[3]), float(parts[4])

        # 회전에 따라 어떤 축이 '높이'가 되는지 판별
        if abs(abs(p) - 1.5708) < 0.1: # Pitch 90도
            effective_height = width
        elif abs(abs(r) - 1.5708) < 0.1: # Roll 90도
            effective_height = depth
        else:
            effective_height = height

        return effective_height / 2.0
    except:
        return 0.0

def format_geometry(model_name, geo_data, default_mesh_name):
    if not geo_data:
        return f"<mesh><uri>model://{model_name}/meshes/{default_mesh_name}</uri></mesh>"

    g_type = geo_data["type"]
    if g_type == "box":
        return f"<box><size>{geo_data['size']}</size></box>"
    elif g_type == "cylinder":
        return f"<cylinder><radius>{geo_data['radius']}</radius><length>{geo_data['length']}</length></cylinder>"
    elif g_type == "sphere":
        return f"<sphere><radius>{geo_data['radius']}</radius></sphere>"
    elif g_type == "mesh":
        scale = geo_data.get('scale', '1 1 1')
        return f"<mesh><uri>model://{model_name}/meshes/{default_mesh_name}</uri><scale>{scale}</scale></mesh>"
    return ""

def generate_sdf_content(model_name, dae_filename, data):
    # 1. Z축 오프셋 계산 (기존 수치 기반)
    z_offset = calculate_z_offset(data["collision"]["pose"], data["collision"]["geo"])

    # 2. 각 Pose 문자열 정제 및 오프셋 적용
    # threshold=0.001 로 설정하여 1mm 미만의 오차는 모두 0으로 처리
    i_pose = clean_and_offset_pose(data['i_pose'], z_offset)
    c_pose = clean_and_offset_pose(data['collision']['pose'], z_offset)
    v_pose = clean_and_offset_pose(data['visual']['pose'], z_offset)

    collision_geo = format_geometry(model_name, data["collision"]["geo"], dae_filename)
    visual_geo = format_geometry(model_name, data["visual"]["geo"], dae_filename)

    return f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <link name="base_link">
      <allow_auto_disable>1</allow_auto_disable>
      <laser_retro>150</laser_retro>

      <visual name="visual">
        <pose>{v_pose}</pose>
        <cast_shadows>1</cast_shadows>
        <geometry>{visual_geo}</geometry>
      </visual>

      <inertial>
        <pose>{i_pose}</pose>
        <mass>{data['mass']}</mass>
        <inertia>
          <ixx>{data['inertia']['ixx']}</ixx>
          <ixy>{data['inertia']['ixy']}</ixy>
          <ixz>{data['inertia']['ixz']}</ixz>
          <iyy>{data['inertia']['iyy']}</iyy>
          <iyz>{data['inertia']['iyz']}</iyz>
          <izz>{data['inertia']['izz']}</izz>
        </inertia>
      </inertial>

      <collision name="collision">
        <pose>{c_pose}</pose>
        <geometry>{collision_geo}</geometry>
        <surface>
          <friction>
            <ode>
              <mu>1.0</mu>
              <mu2>1.0</mu2>
            </ode>
          </friction>
          <contact>
            <ode>
              <kp>100000.0</kp>
              <kd>100.0</kd>
              <min_depth>0.001</min_depth>
              <max_vel>0.1</max_vel>
            </ode>
          </contact>
        </surface>
      </collision>
    </link>
  </model>
</sdf>'''


def generate_config_content(model_name):
    return f'''<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author>
    <name>LEE D.W.</name>
    <email>2dongwon@gmail.com</email>
  </author>
  <description>Generate a Gazebo model using a URDF file</description>
</model>'''