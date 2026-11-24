import hashlib, json, re, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
A = R / 'analysis'
geometry = json.loads((A / 'geometry_and_fit.json').read_text(encoding='utf8'))
slicing = json.loads((A / 'slicing_check.json').read_text(encoding='utf8'))
with zipfile.ZipFile(A / 'Base400.gcode.3mf') as z:
    code = z.read('Metadata/plate_1.gcode')
    md5 = z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    assert hashlib.md5(code).hexdigest() == md5
    settings = json.loads(z.read('Metadata/project_settings.config'))
    root = ET.fromstring(z.read('Metadata/slice_info.config'))
    meta = {m.get('key'): m.get('value') for m in root.find('plate').findall('metadata')}
    assert meta['outside'] == 'false' and meta['support_used'] == 'false'
    assert settings['enable_support'] == '0'
    assert settings['printer_model'] == 'Bambu Lab X1 Carbon'
    assert settings['nozzle_diameter'] == ['0.4']
text = code.decode('utf8')
commands = '\n'.join(l.split(';')[0] for l in text.splitlines())
assert not re.search(r'\{[^}]+\}|\[[a-zA-Z_][^]]*\]', commands)
feature = 'Custom'
positions = []
x = y = z = 0.0
relative_e = True
previous_e = 0.0
layers = {}
for line in text.splitlines():
    if line.startswith('; FEATURE: '):
        feature = line[11:].strip()
    s = line.split(';')[0].strip()
    if s == 'M83':
        relative_e = True
    elif s == 'M82':
        relative_e = False
    if not re.match(r'^G(?:0|1|2|3|92)\s', s):
        continue
    fields = {k: float(v) for k, v in re.findall(r'([XYZEF])([-+]?\d*\.?\d+)', s)}
    x, y, z = fields.get('X', x), fields.get('Y', y), fields.get('Z', z)
    if s.startswith('G92'):
        previous_e = fields.get('E', previous_e)
        continue
    extrusion = fields.get('E', 0) if relative_e else fields.get('E', previous_e) - previous_e
    previous_e = fields.get('E', previous_e)
    if extrusion > 0 and feature != 'Custom' and ('X' in fields or 'Y' in fields):
        assert 20 < x < 236 and 20 < y < 236 and 0 < z <= 5.01, (x, y, z, feature)
        positions.append((x, y, z))
        layers[round(z, 3)] = layers.get(round(z, 3), 0) + 1
assert len(layers) == 18 and all(v > 50 for v in layers.values()), layers
assert not re.search(r'; FEATURE: .*Support', text, re.I)
report = {
    'checked_on': '2026-11-13', 'github_main_sha': 'd949a2df31095d3f23e31dd5c5a8c643afc40b5d',
    'github_published_pico_version': '1.11',
    'github_source': 'https://github.com/JavonLoong/suzume-visionpro/releases/tag/complete-project-2026-10-30',
    'delivered_stl_archive': 'D:/虚拟C盘/底座.zip',
    'delivered_stl_count': 1, 'print_quantity': 4,
    'stl_sha256': geometry['sha256'],
    'archive_sha256': hashlib.sha256(Path('D:/虚拟C盘/底座.zip').read_bytes()).hexdigest(),
    'mesh_watertight': True, 'assembly_checks_passed': len(geometry['assembly_checks']),
    'slicer': 'BambuStudio 02.01.01.52 (installed)',
    'gcode_md5_valid': True, 'unresolved_executable_templates': False,
    'toolpath_deposition_inside_bed': True,
    'layer_count': len(layers), 'extrusion_movements_checked': len(positions),
    'support_used': False, 'slice_warning': slicing['warnings'],
    'estimated_seconds_each': slicing['seconds'], 'estimated_grams_each': slicing['grams'],
    'estimated_seconds_all_four': slicing['total_seconds'], 'estimated_grams_all_four': slicing['total_grams'],
    'physical_print_test': False, 'printer_job_started': False,
    'delivery_format_note': 'User delivery is STL only; the G-code archive is internal verification output and is not a new direct-print delivery.'
}
(A / 'final_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
instructions = '''铃芽庭院底座｜2026-11-13

文件：D:/虚拟C盘/底座.zip
压缩包里只有 1 个文件「底座.stl」。它是一块四分之一圆底座，同一文件打印 4 次。
拼好直径 400 mm，厚 5 mm。单块约 199.9 × 199.9 × 5 mm，平底朝下，孔朝上。
不能在 256 mm 的板上一次打印整个直径 400 mm 的圆；这版每次打印一块，共四盘。

建议切片设置（此次已用这些设置实际生成打印路径）：
拓竹 X1 Carbon；0.4 mm 喷嘴；白色 PLA（校验时为 Bambu PLA Basic）；纹理 PEI 板。
层高 0.28 mm；3 圈墙；10% 螺旋填充；顶底各 3 层；关闭支撑；5 mm 外沿裙边。
喷嘴 220°C、热床 55°C 是本次材料预设。更换线材请使用对应材料设置。
每块预估 1 小时 48 分 39 秒、89.31 克；四块共 7 小时 14 分 36 秒、357.24 克。
这些是切片估算，实际包含设备准备、流量校准等差异。
切片器产生 bed_temperature_too_high_than_filament 提示；未修改原 PLA/纹理 PEI 温度预设。

安装：
1. 先打印一块，使用原有 3 mm 定位销试插；确认本机打印松紧后，再重复打印余下三块。
2. 四块各旋转 90° 围成圆，使用原「第一组」第 4 盘里的 8 个拼接键连接。
3. 拼接键槽允许少量间隙，最终薄涂适用于 PLA 的胶固定。拼接键不是自动锁紧扣。
4. 使用同一盘已有的 32 个定位销：外圈 16 个装墙体，内圈 16 个装钢架。
5. 白门台阶位于底座中心，底面粘接；门扇和铰链不要粘死。
6. 搬运时托住底座下方。不要只提墙体或只抓一块底座悬空搬动整套庭院。

检查范围：
STL 为一个闭合实体；底板 5 mm；定位孔为盲孔，孔底保留 2.8 mm；拼接槽底保留 2.9 mm。
与最新 WM2 墙体、钢架、门以及定位销/拼接键共 65 项几何装配检查通过。
实际切片成功，18 层，无支撑，无打印范围越界；打印路径校验码和模板检查通过。
尚未实体试打，不能保证未校准机器上的尺寸、首层粘附或最终抗弯强度。
此底座用于干式模型展示，拼缝不作盛水密封设计。

为了缩短打印时间，本版保留平整表面，没有叠加旧底盘的碎石起伏。
需要水面观感时，可后续做表面上色或另贴薄膜；暂未生成贴膜尺寸文件。
检查记录、切片验证文件和可继续修改的 Blender 文件：
D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/print-base-400mm-20261113
'''
(R / '打印与装配说明.txt').write_text(instructions, encoding='utf8')
print('FINAL_VERIFICATION_PASS', len(positions), 'deposition moves', len(layers), 'layers', flush=True)
