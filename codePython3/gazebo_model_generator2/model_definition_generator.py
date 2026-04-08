def clean_pose(pose_str, threshold=0.001):
    """URDF에서 가져온 포즈 문자열을 정제합니다. (불필요한 Z오프셋 제거)"""
    parts = pose_str.split()
    if len(parts) < 6: return pose_str

    cleaned_parts = []
    for val_str in parts:
        val = float(val_str)
        if abs(val) < threshold:
            cleaned_parts.append("0.00000")
        else:
            cleaned_parts.append(f"{val:.5f}")
    return " ".join(cleaned_parts)

def format_geometry(model_name, geo_data, default_mesh_name):
    """URDF 데이터를 SDF 기하 구조 태그로 변환하며 스케일을 반영합니다."""
    if not geo_data:
        return f"<mesh><uri>model://{model_name}/meshes/{default_mesh_name}</uri><scale>1 1 1</scale></mesh>"
    
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
    return f"<mesh><uri>model://{model_name}/meshes/{default_mesh_name}</uri></mesh>"

def generate_material_content(mat_info, fallback_image_filename):
    """DAE에서 추출한 파일명을 최우선으로 사용하여 스크립트를 생성합니다."""
    blocks = []
    for mat_id, info in mat_info.items():
        actual_image = info.get("texture_file", "none")
        
        # DAE에 이름이 없고, 사용자가 이미지를 선택했다면 사용자가 선택한 이미지 적용
        if actual_image == "none" and fallback_image_filename != "none":
            actual_image = fallback_image_filename

        if info["has_texture"] and actual_image != "none":
            content = f"texture_unit {{ texture {actual_image} }}"
        else:
            c = info["diffuse_color"]
            content = f"ambient {c}\n      diffuse {c}\n      specular 0.5 0.5 0.5 1.0 12.5"
            
        blocks.append(f"material {mat_id}\n{{\n  technique\n  {{\n    pass\n    {{\n      {content}\n    }}\n  }}\n}}")
    return "\n\n".join(blocks)

def generate_sdf_content(model_name, dae_filename, data):
    """SDF 파일 생성 (URDF 포즈를 그대로 신뢰함)"""
    v_pose = clean_pose(data['visual']['pose'])
    c_pose = clean_pose(data['collision']['pose'])
    i_pose = clean_pose(data['i_pose'])

    v_geo = format_geometry(model_name, data["visual"]["geo"], dae_filename)
    c_geo = format_geometry(model_name, data["collision"]["geo"], dae_filename)

    return f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <link name="base_link">
      <allow_auto_disable>1</allow_auto_disable>
      <laser_retro>150</laser_retro>
      
      <visual name="visual">
        <pose>{v_pose}</pose>
        <cast_shadows>1</cast_shadows>
        <geometry>{v_geo}</geometry>
        <material>
          <script>
            <uri>model://{model_name}/materials/scripts</uri>
            <uri>model://{model_name}/materials/textures</uri>
          </script>
        </material>
      </visual>

      <inertial>
        <pose>{i_pose}</pose>
        <mass>{data['mass']}</mass>
        <inertia>
          <ixx>{data['inertia']['ixx']}</ixx><ixy>{data['inertia']['ixy']}</ixy><ixz>{data['inertia']['ixz']}</ixz>
          <iyy>{data['inertia']['iyy']}</iyy><iyz>{data['inertia']['iyz']}</iyz><izz>{data['inertia']['izz']}</izz>
        </inertia>
      </inertial>

      <collision name="collision">
        <pose>{c_pose}</pose>
        <geometry>{c_geo}</geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
          <contact>
            <ode><kp>100000.0</kp><kd>100.0</kd><min_depth>0.001</min_depth><max_vel>0.1</max_vel></ode>
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
  <author><name>LEE D.W.</name></author>
  <description>Auto-generated Gazebo model from URDF and DAE</description>
</model>'''