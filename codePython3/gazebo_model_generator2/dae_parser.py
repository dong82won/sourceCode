import xml.etree.ElementTree as ET

def extract_material_info(dae_path):
    """DAE 파일의 네임스페이스를 자동 감지하고 재질별 텍스처(실제 파일명 포함)와 색상 정보를 추출합니다."""
    try:
        tree = ET.parse(dae_path)
        root = tree.getroot()

        # 네임스페이스 자동 추출
        ns_uri = ""
        if root.tag.startswith("{"):
            ns_uri = root.tag.split("}")[0].strip("{")
        
        ns = {'ns': ns_uri} if ns_uri else {}
        find_p = lambda p: ('.//ns:' + p.replace('/', '/ns:')) if ns_uri else ('.//' + p)

        mat_info = {}
        for mat in root.findall(find_p('library_materials/material'), ns):
            mat_id = mat.get('id')
            inst_eff = mat.find('ns:instance_effect' if ns_uri else 'instance_effect', ns)
            
            if inst_eff is None: continue
            url = inst_eff.get('url')
            if not url: continue
            
            eff_id = url.replace('#', '')
            
            eff_path = f".//ns:library_effects/ns:effect[@id='{eff_id}']" if ns_uri else f".//library_effects/effect[@id='{eff_id}']"
            effect = root.find(eff_path, ns)
            if effect is None: continue

            diffuse = effect.find('.//ns:diffuse' if ns_uri else './/diffuse', ns)
            if diffuse is None: continue

            has_texture = diffuse.find('ns:texture' if ns_uri else 'texture', ns) is not None
            
            # [핵심] DAE 내부에서 텍스처 이미지 파일명 직접 추출
            texture_file = "none"
            if has_texture:
                img_tags = root.findall(find_p('library_images/image/init_from'), ns)
                if img_tags and img_tags[0].text:
                    texture_file = img_tags[0].text.strip()
            
            color_vec = "1.0 1.0 1.0 1.0"
            color_tag = diffuse.find('ns:color' if ns_uri else 'color', ns)
            if color_tag is not None and color_tag.text:
                color_vec = color_tag.text.strip()

            mat_info[mat_id] = {
                "has_texture": has_texture, 
                "texture_file": texture_file, 
                "diffuse_color": color_vec
            }
            
        return mat_info
    except Exception as e:
        print(f"DAE 분석 실패: {e}")
        return {}