import xml.etree.ElementTree as ET

def parse_urdf_values(urdf_path):
    try:
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        link = root.find('.//link')
        if link is None:
            return None, "URDF 내에서 <link> 태그를 찾을 수 없습니다."

        def get_pose(element):
            if element is None: return "0 0 0 0 0 0"
            origin = element.find('origin')
            if origin is None: return "0 0 0 0 0 0"
            return f"{origin.get('xyz', '0 0 0')} {origin.get('rpy', '0 0 0')}"

        def get_geometry_data(geom_element):
            """geometry 태그 내부의 형상 정보를 분석하여 반환합니다."""
            if geom_element is None: return None
            
            # 1. Box
            box = geom_element.find('box')
            if box is not None:
                return {"type": "box", "size": box.get('size', '1 1 1')}
            
            # 2. Cylinder
            cylinder = geom_element.find('cylinder')
            if cylinder is not None:
                return {
                    "type": "cylinder", 
                    "radius": cylinder.get('radius', '0.5'), 
                    "length": cylinder.get('length', '1.0')
                }
            
            # 3. Sphere
            sphere = geom_element.find('sphere')
            if sphere is not None:
                return {"type": "sphere", "radius": sphere.get('radius', '0.5')}
            
            # 4. Mesh
            mesh = geom_element.find('mesh')
            if mesh is not None:
                return {"type": "mesh", "filename": mesh.get('filename', ''), "scale": mesh.get('scale', '1 1 1')}
            
            return None

        # 기본 데이터 구조
        data = {
            "mass": "0.1",
            "i_pose": "0 0 0 0 0 0",
            "inertia": {"ixx":"0.01", "ixy":"0", "ixz":"0", "iyy":"0.01", "iyz":"0", "izz":"0.01"},
            "collision": {"pose": "0 0 0 0 0 0", "geo": None},
            "visual": {"pose": "0 0 0 0 0 0", "geo": None}
        }

        # Inertial 정보 추출
        inertial = link.find('inertial')
        if inertial is not None:
            mass_tag = inertial.find('mass')
            if mass_tag is not None: data["mass"] = mass_tag.get('value', '0.1')
            data["i_pose"] = get_pose(inertial)
            inertia = inertial.find('inertia')
            if inertia is not None:
                for k in data["inertia"].keys():
                    data["inertia"][k] = inertia.get(k, data["inertia"][k])

        # Collision 정보 추출
        collision = link.find('collision')
        if collision is not None:
            data["collision"]["pose"] = get_pose(collision)
            data["collision"]["geo"] = get_geometry_data(collision.find('geometry'))

        # Visual 정보 추출
        visual = link.find('visual')
        if visual is not None:
            data["visual"]["pose"] = get_pose(visual)
            data["visual"]["geo"] = get_geometry_data(visual.find('geometry'))

        return data, None
    except Exception as e:
        return None, str(e)