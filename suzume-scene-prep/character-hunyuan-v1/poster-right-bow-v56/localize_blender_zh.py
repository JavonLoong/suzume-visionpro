"""Create a Chinese-labelled V56 copy; leave the source and open edits intact."""
import bpy
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "铃芽之旅_v56_中文版.blend"

WORKSPACES = {
    "Layout": "布局", "Modeling": "建模", "Sculpting": "雕刻",
    "UV Editing": "UV编辑", "Texture Paint": "纹理绘制", "Shading": "着色",
    "Animation": "动画", "Rendering": "渲染", "Compositing": "合成",
    "Geometry Nodes": "几何节点", "Scripting": "脚本",
}
EXACT = {
    **WORKSPACES,
    "Daytime circular hotel": "白昼·环形废弃酒店",
    "Night meadow through the door": "门后异世界·夜色草原",
    "Official poster courtyard v38": "官方海报·庭院场景",
    "Complete six-panel white door and frame": "完整六格白门与门框",
    "Animated door leaf and hinges": "可开合门扇与铰链",
    "Branching tree crowns surrounding the ruined hotel": "酒店四周树冠",
    "Circular ruined hotel with exterior entrance": "带外部入口的环形废弃酒店",
    "Individual three-dimensional ivy leaves": "独立三维常春藤叶片",
    "Brick and masonry debris": "砖石碎块",
    "Flooded polygon flagstones and broken slabs": "淹水石板与破碎板块",
    "Live planar reflective shallow water": "浅水与平面反射",
    "Scene axes — meters": "场景坐标·单位为米",
    "Suzume — Hunyuan four-view reconstruction": "铃芽·混元四视图重建",
    "Suzume — portion inside the otherworld": "铃芽·已进入异世界的部分",
    "Suzume Hunyuan rig": "铃芽·混元骨架",
    "Suzume Hunyuan textured surface": "铃芽·混元贴图模型",
    "Door front camera": "门前相机", "Reference camera": "参考相机",
    "Native enclosing night sky": "环绕夜空", "Forest trunks": "森林树干",
    "Rolling meadow ground": "起伏草原地面", "Modeled flower stems": "立体花茎",
    "Individual meadow flowers": "草原独立花朵", "Spatial grass blades": "三维草叶",
    "Spatial luminous stars": "立体发光星辰", "ViewLayer": "视图层",
}
PHRASES = {
    "I-section": "工字钢", "I-column": "工字钢柱", "I-beam": "工字钢梁",
    "reference-shaped": "参照轮廓", "reference-calibrated": "参照校准",
    "three-dimensional": "三维", "four-view": "四视图", "six-panel": "六格",
    "lower-storey": "下层", "upper-storey": "上层", "through-openings": "贯通开口",
    "steel-climbing": "攀钢", "linked geometry": "关联几何体",
    "solid mesh": "实体网格", "vertex pigments": "顶点色",
    "ray portal": "光线传送门", "fixed film pigments": "校准电影色彩",
    "water tank": "水箱", "service house": "设备间", "foot shoe": "底座",
    "inner bead": "内侧压条", "back wall foot": "后墙墙脚", "side wall foot": "侧墙墙脚",
    "front camera": "正面相机", "pull handle": "拉手", "roof contact": "屋面连接处",
    "lower main": "下部主管", "upper return": "上部回弯管", "fan spoke": "扇形辐条",
    "fan glazing": "扇形玻璃", "leaf frame": "门扇框", "door leaf": "门扇",
    "window fan": "窗式风扇", "main collar": "主管抱箍", "return collar": "回弯管抱箍",
    "courtyard half": "庭院侧", "otherworld half": "异世界侧",
    "entered portion": "进入异世界部分", "lower story": "下层", "upper window": "上层窗户",
}
WORDS_TEXT = """
aged=老化 amber=琥珀色 ambientlight=环境光 anchor=锚固 and=与 animated=动画 animation=动画 annular=环形 aperture=开口 arcade=拱廊 arch=拱门 arched=拱形 archside=拱侧 around=周围 at=位于 attached=附着 awning=雨棚 axes=坐标轴
back=后部 balcony=阳台 band=带 bank=岸 barrette=发夹 base=基座 basin=水池 bay=开间 bead=压条 beam=梁 bed=底 bend=弯头 bent=弯曲 between=之间 beyond=后方 billows=云团 blade=叶片 blades=叶片 blue=蓝色 board=木板 boards=木板 bolt=螺栓 bow=弯梁 bowed=弯曲 brace=支撑 bracket=托架 branching=分枝 brick=砖 broad=宽 broken=破损 brown=棕色
calibrated=校准 camera=相机 cap=顶盖 capital=柱头 casing=外壳 catchlight=眼睛高光 center=中心 central=中央 chair=椅子 cheek=侧板 circular=环形 clerestory=高侧窗 climbing=攀附 closed=封闭 cloud=云 collapsed=坍塌 collar=抱箍 color=色彩 colors=色彩 column=柱 complete=完整 compositing=合成 concrete=混凝土 connections=连接件 contact=连接 continuation=延伸 continuous=连续 cool=冷色 cornice=檐口 corrected=修正 corroded=腐蚀 course=层 courtyard=庭院 cracked=开裂 creeper=匍匐植物 creeping=攀爬 cross=交叉 crossbar=横杆 crossed=交叉 crown=顶部 crowns=树冠 curb=路缘 curved=弧形
damaged=受损 dark=深色 daylight=日光 daytime=白昼 debris=碎块 dense=密集 diagonal=斜向 diamond=菱形 dimensional=维 directionallight=平行光 discarded=废弃 distant=远景 divider=隔板 dome=穹顶 door=门 doorway=门洞 double=双联 drainpipe=排水管 drip=滴水线
ear=耳朵 edge=边缘 edges=边缘 editable=可编辑 editing=编辑 enclosing=环绕 entered=已进入 entering=进入 entrance=入口 entry=入口 equipment=设备 exposed=外露 exterior=外部 eye=眼睛 eyelashes=睫毛
facade=立面 faces=面 faded=褪色 fan=扇形 fascia=檐板 fill=补光 film=电影 fine=精细 first=第一 fixed=固定 fixing=固定 flagstones=石板 flange=翼缘 flooded=淹水 floor=地板 flower=花 flowers=花朵 foliage=枝叶 foot=底脚 footing=柱脚 footings=柱脚 foreground=前景 forest=森林 foundation=基础 four=四 fragment=碎片 frame=框架 front=前方
gap=缺口 geometry=几何 glass=玻璃 glazing=玻璃 glow=辉光 gold=金色 graded=分层 grass=草 gray=灰色 grey=灰色 grid=格栅 grille=格栅 groove=凹槽 ground=地面 grounded=落地 group=组 growth=植被 guardrail=护栏
hair=头发 half=半部 handle=把手 hanging=悬挂 head=头部 hemispherelight=半球光 hinges=铰链 hollow=空心 hood=雨罩 horizon=地平线 horizontal=水平 hotel=酒店 house=房屋 hunyuan=混元 i=工字 in=内 individual=独立 infill=填板 inner=内侧 insert=嵌板 inside=内部 interior=室内 iris=虹膜 irregular=不规则 isolated=孤立 ivy=常春藤 jamb=窗侧框 joint=接头
ladder=梯子 landing=落脚处 large=大型 layered=分层 layout=布局 leaf=叶片 leaves=叶片 ledge=台沿 left=左侧 leg=腿 linked=关联 lintel=过梁 live=实时 localized=局部 long=长 low=低矮 lower=下部 luminous=发光
main=主 margin=边缘 masonry=砌体 material=材质 mathematical=数学建模 meadow=草原 measured=测量 mesh=网格 metal=金属 meters=米 middle=中部 mist=薄雾 mixed=混合 modeled=建模 modeling=建模 molded=饰线 molding=饰线 moonlight=月光 movie=电影 mullion=窗梃
narrow=狭窄 native=原生 night=夜晚 nodes=节点 nostril=鼻孔 observed=参照 offset=偏移 oculus=圆窗 official=官方 on=上 open=开启 openings=开口 or=或 otherworld=异世界 outer=外侧
paint=漆 pale=浅色 panel=面板 parapet=女儿墙 part=部件 partly=局部 patch=簇 petiole=叶柄 pier=壁柱 pigments=色彩 pipe=管道 pipes=管道 planar=平面 plants=植物 plaster=灰泥 plate=底板 podium=基台 pointed=尖拱 pointlight=点光源 polygon=多边形 portal=传送门 portico=门廊 portion=部分 post=立柱 poster=海报 projection=投影 props=道具 prototype=原型 prototypes=原型 pull=拉 pupil=瞳孔
radial=放射状 rail=横杆 railing=栏杆 ray=光线 reached=通向 realized=实体化 realm=世界 rear=后方 recess=凹位 recessed=内凹 reconstructed=重建 reconstruction=重建 rectangle=矩形 rectangular=矩形 red=红色 reference=参考 reflective=反射 removed=移除 rendering=渲染 restored=修复 retained=保留 return=回弯 rib=肋 ridge=脊 rig=骨架 right=右侧 rim=边框 ring=环 rod=杆 rods=杆 rolled=卷边 rolling=起伏 roof=屋顶 rooftop=屋顶 room=房间 rooms=房间 root=根部 ruined=废弃 rust=锈色 rustdark=深锈色 rusted=生锈
sagging=下垂 scene=场景 scripting=脚本 sculpting=雕刻 seat=座面 second=第二 section=截面 sector=扇区 sediment=沉积物 service=设备 shaded=背阴 shading=着色 shadow=阴影 shallow=浅水 shaped=轮廓 shard=碎片 shoe=底座 shoreline=岸线 short=短 shrub=灌木 side=侧面 sill=窗台 six=六 skin=皮肤 sky=天空 slab=板 slabs=板块 slanted=倾斜 slender=细长 sloped=坡面 sloping=倾斜 small=小型 soft=柔和 solid=实体 source=源 spatial=空间 splayed=外倾 spoke=辐条 stair=楼梯 standpipe=立管 starlight=星光 stars=星辰 steel=钢 steelwork=钢结构 stem=茎 stems=茎 step=台阶 stile=竖框 stone=石 stones=石块 storey=层 story=层 strap=固定带 stratus=层云 strip=条 structural=结构 structure=结构 stub=残段 sunken=下沉 sunlight=阳光 support=支座 supporting=支撑 supports=支座 surface=表面 surround=外框 surrounding=四周 surviving=残存 suzume=铃芽 synchronized=同步
tank=水箱 terrain=地形 texture=纹理 textured=贴图 the= thicket=灌丛 thin=细 three=三 through=穿过 tie=拉杆 to=转为 trail=藤蔓 transition=过渡 transom=窗楣 tree=树 trim=饰边 triple=三联 trunks=树干 twilight=暮光 two=双
upper=上部 upright=竖杆 vertex=顶点 vertical=竖直 view=视图 vine=藤蔓 visible=可见 volume=体积 walkway=步道 wall=墙 warm=暖色 water=水 waterfront=水岸 weathered=风化 web=腹板 wet=潮湿 white=白色 wide=宽幅 window=窗户 with=带 world=世界 worn=磨损
"""
WORDS = dict(item.split("=", 1) for item in WORDS_TEXT.split())
WORDS.update({"uv": "UV", "agx": "AgX", "cycles": "Cycles"})
PHRASES.update({key: value for key, value in EXACT.items() if key not in WORKSPACES})
PHRASE_RE = re.compile("|".join(re.escape(k) for k in sorted(PHRASES, key=len, reverse=True)), re.I)
PHRASES_CASE = {k.casefold(): v for k, v in PHRASES.items()}
UNKNOWN = set()

def translate(name):
    if name in EXACT:
        return EXACT[name]
    value = PHRASE_RE.sub(lambda m: PHRASES_CASE[m.group().casefold()], name)
    value = re.sub(r"\bv(\d+)\b", r"第\1版", value)
    def word(m):
        key = m.group().casefold()
        if key not in WORDS:
            UNKNOWN.add(m.group())
        return WORDS.get(key, m.group())
    value = re.sub(r"[A-Za-z]+", word, value)
    return re.sub(r"\s+", "", value).replace("—", "·")

groups = ("workspaces", "scenes", "collections", "objects", "materials", "node_groups")
for group in groups:
    for item in getattr(bpy.data, group):
        translate(item.name)
if UNKNOWN:
    raise RuntimeError("Untranslated name tokens: " + repr(sorted(UNKNOWN)))

config = Path(bpy.utils.user_resource("CONFIG"))
prefs_file = config / "userpref.blend"
if prefs_file.exists():
    backup = HERE / ("userpref_before_zh_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".blend")
    shutil.copy2(prefs_file, backup)
prefs = bpy.context.preferences.view
prefs.language = "zh_HANS"
for prop in ("use_translate_interface", "use_translate_tooltips", "use_translate_new_dataname", "use_translate_reports"):
    setattr(prefs, prop, True)
bpy.ops.wm.save_userpref()

changes = []
for group in groups:
    for item in list(getattr(bpy.data, group)):
        original = item.name
        chinese = translate(original)
        if chinese != original:
            # Preserve reverse mapping outside the file, without changing model data.
            item.name = chinese
            changes.append({"type": group, "original": original, "chinese": item.name})
for scene in bpy.data.scenes:
    for layer in scene.view_layers:
        if layer.name == "ViewLayer":
            layer.name = "视图层"

mapping_path = HERE / "中文名称对照.json"
mapping_path.write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
result = {
    "file": str(OUTPUT), "language": prefs.language,
    "translations": {key: getattr(prefs, key) for key in ("use_translate_interface", "use_translate_tooltips", "use_translate_new_dataname", "use_translate_reports")},
    "workspaces": [w.name for w in bpy.data.workspaces],
    "counts": {group: len(getattr(bpy.data, group)) for group in groups},
    "renamed": len(changes), "untranslated_tokens": sorted(UNKNOWN),
}
(HERE / "中文设置验证.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("CHINESE_LOCALIZATION_COMPLETE", json.dumps(result, ensure_ascii=True))
