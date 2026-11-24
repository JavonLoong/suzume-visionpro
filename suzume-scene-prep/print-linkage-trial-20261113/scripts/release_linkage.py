import json,hashlib,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'analysis';D=R/'交付';D.mkdir(exist_ok=True)
m=json.loads((A/'linkage_manifest.json').read_text(encoding='utf8'))
checks=json.loads((A/'slicing_checks.json').read_text(encoding='utf8'));index={r['id']:r for r in checks}
assert len(m['parts'])==3 and len(m['checks'])==1275
for r in m['parts']:
    c=index[r['id']];assert c['exit_code']==0 and c['outside']=='false' and c['md5_valid']
    assert hashlib.sha256(Path(r['stl_path']).read_bytes()).hexdigest()==r['sha256']==c['stl_sha256']
out=D/'拉杆.zip';assert not out.exists()
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for r in m['parts']:z.write(r['stl_path'],Path(r['stl_path']).name)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None and len(z.namelist())==3 and all('/' not in n and n.endswith('.stl') for n in z.namelist())
    for r in m['parts']:assert hashlib.sha256(z.read(Path(r['stl_path']).name)).hexdigest()==r['sha256']
old={'白门.zip':'df86eea53d00c473492eeb2713d4f6a66ca48a5ea2c359f7d273d87433f3ffaf','三档.zip':'7732f9039d02c50139fc4cf4dfb688178356e7fc4aca28cf14b4016c110a8586','底座.zip':'e98dcc5b71dae350caa7175b47d577df9ee09761bc2520b56ed05155c56a6114'}
for name,digest in old.items():assert hashlib.sha256((Path('D:/虚拟C盘')/name).read_bytes()).hexdigest()==digest
report={'archive':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'stl_only':True,'native_slicing':checks,'original_archives_unchanged':old,'actual_print_test':False,'servo_mount_finished':False}
(A/'release_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
time_lines='\n'.join(f"{r['id']}：约 {round(r['seconds']/60)} 分钟，{r['grams']:.2f} 克。" for r in checks)
note='''门背拉杆试配 · 2026-11-13

已明确：用户说的约 1 mm，是原装白色摇臂上插钢丝的孔，不是舵机输出轴。
传动路线：舵机原摇臂 → 钢丝推拉杆 → 门背一体摇臂 → 门扇。
原有 2 mm 金属轴仅支撑门的转动，不需要与舵机直接对插。
门背摇臂与门扇做成同一打印件，避免套在光轴上的小接头打滑。

拉杆.zip 只有三个 STL：门扇50.stl、门扇60.stl、门扇70.stl。
选择与现有门框匹配的一档，只换门扇即可；门框、插座板和 50 cm 底座沿用原件。
这是门侧试配版，不是舵机安装已经完成的整机打印包。
图中橙色只标出新增部位，打印时整个门扇仍是单色白模。

门侧参数：2 mm 厚摇臂，距门轴中心 6 / 9 / 12 mm 三个孔位，名义孔径 1.2 mm。
拉杆先以 0.8 mm 金属钢丝为候选；需试穿原摇臂约 1 mm 小孔，能自由转动后再定。
钢丝不在 STL 中，不能用 1 mm 打印塑料细杆代替支撑轴或直接当作已验证传动件。
拉杆两端可用 Z 形弯头防脱，每个连接点需能在孔里转动。
原 2 mm 金属轴仍另备，穿入原 2.4 mm 孔；需在固定门框侧限位，避免轴上下滑出。

已做的检查：
三档门扇都是封闭的单个实体、面方向一致、没有自交；新增摇臂没有删减原门的细节。
每隔 1° 检查门扇和门框、插座板，覆盖 0～105°；门扇最低点高于底板。
对每档的三个拉杆孔逐一检查了候选 0.8 mm 拉杆、竖直连接段和短防脱弯头的运动。
三档均完成本机 X1 Carbon 切片及 G-code 校验，未越界。

计算示意的假设，不是量过的舵机尺寸：
舵机轴在门轴右边 40 mm；两边选用相同孔距；摇臂和拉杆的转动平面等高。
关门时摇臂相对两轴连线为 135°；门打开 105° 时剩 30°，计算范围内没有转到一条直线的卡住位置。
这里 40 mm 是两连接销中心之间的长度，不包括弯钩，不能据此直接截断钢丝。
若舵机孔距与门侧孔距不同，需要重新算行程；不能承诺舵机转多少度，门就转多少度。
现有底座下方只有 5 mm 空隙，不能据此认为 20～30 mm 舵机能直接装进去。

定舵机支架和拉杆长度前还需要：
1. 舵机型号，或外壳长宽高、安装耳孔位置、摇臂平面高度。
2. 原摇臂中心螺丝至选用小孔中心的距离。
3. 确认钢丝能顺畅穿过小孔，以及选择侧后安装空间。
拿到这些尺寸后再定安装盒、拉杆的实际长度和零位。
先让未接拉杆的舵机停在中位，再进行机械试配；从小幅行程开始。
105° 是模型检查范围，不是可以直接下发的舵机控制参数。

切片验证设置：X1 Carbon、0.4 mm 喷嘴、PLA、0.12 mm 层高、3 圈墙、15% gyroid、普通自动支撑、3 mm 边裙。
保持毫米、100% 尺寸及文件中的平放方向。STL 不包含机器参数，导入后需要重新切片。
支撑上下间距均 0.12 mm，拆支撑时保护门背小孔和门面细边线。
切片器保留 bed_temperature_too_high_than_filament 提示（PLA / 55℃ 热床），无打印范围越界。
时间和重量均为切片估计，未实打、未接实际舵机测试。

'''+time_lines+'''

参考资料：Pololu，舵机输出轴与摇臂的结构说明。
https://www.pololu.com/blog/13/gettin-all-up-in-your-servos
本设计保留原装摇臂，不仿制未知齿形的舵机输出端。
'''
(R/'试配说明.txt').write_text(note,encoding='utf-8-sig')
print('LINKAGE_RELEASE_PASS',report['sha256'],flush=True)
