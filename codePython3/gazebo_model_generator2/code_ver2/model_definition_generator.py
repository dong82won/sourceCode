import math

def clean_and_offset_pose(pose_str, z_offset=0.0, threshold=0.001):
    parts = pose_str.split()
    if len(parts) < 6: return pose_str

    cleaned_parts = []
    for i, val_str in enumerate(parts):
        val = float(val_str)
        if i == 2:
            val += z_offset
        if abs(val) < threshold:
            cleaned_parts.append("0.00000")
        else:
            cleaned_parts.append(f"{val:.5f}")
    return " ".join(cleaned_parts)

def calculate_z_offset(pose_str, geo_data):
    if not geo_data or geo_data.get("type") != "box":
        return 0.0
    try:
        size = [float(s) for s in geo_data["size"].split()]
        width, depth, height = size
        parts = pose_str.split()
        r, p = float(parts[3]), float(parts[4])

        if abs(abs(p) - 1.5708) < 0.1:
            effective_height = width
        elif abs(abs(r) - 1.5708) < 0.1:
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

# 추가된 함수: .material 파일 내용 생성
def generate_material_content(model_name, image_filename):
    # 파이썬 f-string에서 중괄호 {}를 출력하려면 {{ }} 두 번 써야 합니다.
    return f"""material {model_name}/Diffuse
{{
  technique
  {{
    pass
    {{
      texture_unit
      {{
        texture {image_filename}
      }}
    }}
  }}
}}"""

# 수정된 함수: material 태그 지원
def generate_sdf_content(model_name, dae_filename, data, image_filename=None):
    z_offset = calculate_z_offset(data["collision"]["pose"], data["collision"]["geo"])

    i_pose = clean_and_offset_pose(data['i_pose'], z_offset)
    c_pose = clean_and_offset_pose(data['collision']['pose'], z_offset)
    v_pose = clean_and_offset_pose(data['visual']['pose'], z_offset)

    collision_geo = format_geometry(model_name, data["collision"]["geo"], dae_filename)
    visual_geo = format_geometry(model_name, data["visual"]["geo"], dae_filename)

    # 이미지가 선택되었다면 SDF에 material 태그 추가
    material_block = ""
    if image_filename:
        material_block = f"""
        <material>
          <script>
            <uri>model://{model_name}/materials/scripts</uri>
            <uri>model://{model_name}/materials/textures</uri>
            <name>{model_name}/Diffuse</name>
          </script>
        </material>"""

    return f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <link name="base_link">
      <allow_auto_disable>1</allow_auto_disable>
      <laser_retro>150</laser_retro>

      <visual name="visual">
        <pose>{v_pose}</pose>
        <cast_shadows>1</cast_shadows>
        <geometry>{visual_geo}</geometry>{material_block}
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