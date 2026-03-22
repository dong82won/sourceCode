# content.py
import xml.etree.ElementTree as ET
import os

def get_dae_size(dae_path):
    """
    DAE 파일의 모든 노드를 탐색하여 변환 행렬(Matrix)이 적용된 
    실제 물리적 Bounding Box 크기를 계산합니다.
    """
    try:
        tree = ET.parse(dae_path)
        root = tree.getroot()
        ns = {'ns': 'http://www.collada.org/2005/11/COLLADASchema'}

        # 1. 모든 노드의 행렬(Matrix) 정보 수집
        # 모델이 여러 조각(Node)으로 나뉘어 각각 스케일이 다를 수 있음을 고려합니다.
        all_min_x, all_max_x = [], []
        all_min_y, all_max_y = [], []
        all_min_z, all_max_z = [], []

        for node in root.findall(".//ns:visual_scene/ns:node", ns):
            matrix_elem = node.find("ns:matrix", ns)
            scale_x, scale_y, scale_z = 1.0, 1.0, 1.0
            
            if matrix_elem is not None:
                m = [float(x) for x in matrix_elem.text.split()]
                # 행렬에서 각 축의 스케일 값 추출
                scale_x = abs(m[0]) if m[0] != 0 else abs(m[2])
                scale_y = abs(m[5])
                scale_z = abs(m[10]) if m[10] != 0 else abs(m[8])

            # 해당 노드와 연결된 geometry의 정점 찾기
            instance_geo = node.find("ns:instance_geometry", ns)
            if instance_geo is not None:
                geo_id = instance_geo.get("url").replace("#", "")
                geo = root.find(f".//ns:geometry[@id='{geo_id}']", ns)
                if geo is not None:
                    pos_array = geo.find(".//ns:float_array", ns)
                    if pos_array is not None and pos_array.text:
                        coords = [float(x) for x in pos_array.text.split()]
                        xs = [x * scale_x for x in coords[0::3]]
                        ys = [y * scale_y for y in coords[1::3]]
                        zs = [z * scale_z for z in coords[2::3]]
                        
                        all_min_x.append(min(xs)); all_max_x.append(max(xs))
                        all_min_y.append(min(ys)); all_max_y.append(max(ys))
                        all_min_z.append(min(zs)); all_max_z.append(max(zs))

        if not all_min_x:
            return 0.1, 0.1, 0.1

        size_x = max(all_max_x) - min(all_min_x)
        size_y = max(all_max_y) - min(all_min_y)
        size_z = max(all_max_z) - min(all_min_z)
        
        return round(size_x, 4), round(size_y, 4), round(size_z, 4)
    except Exception as e:
        print(f"⚠️ 분석 오류: {e}")
        return 0.1, 0.1, 0.1

def generate_config_content(model_name, dae_filename):
    return f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>LEE D.W.</name><email>2dongwon@gmail.com</email></author>
  <description>Auto-generated from {dae_filename}</description>
</model>"""

def generate_sdf_content(model_name, dae_full_path):
    sx, sy, sz = get_dae_size(dae_full_path)
    mass = 1.0 
    
    # 관성 모멘트 계산
    ixx = (1/12) * mass * (sy**2 + sz**2)
    iyy = (1/12) * mass * (sx**2 + sz**2)
    izz = (1/12) * mass * (sx**2 + sy**2)
    
    # 핵심: 모델이 바닥으로 떨어지지 않도록 높이(sz)의 절반만큼 Z축을 올림
    z_pose = sz / 2

    return f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <static>false</static>
    <link name="link">
      <pose>0 0 {z_pose:.4f} 0 0 0</pose>
      <inertial>
        <mass>{mass}</mass>
        <inertia>
          <ixx>{ixx:.6f}</ixx><ixy>0</ixy><ixz>0</ixz>
          <iyy>{iyy:.6f}</iyy><iyz>0</iyz>
          <izz>{izz:.6f}</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry>
          <box><size>{sx} {sy} {sz}</size></box>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <mesh><uri>model://{model_name}/meshes/model.dae</uri></mesh>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>"""