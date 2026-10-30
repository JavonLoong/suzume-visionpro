from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, uuid
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Assets/Resources/ControllerGuide';OUT.mkdir(parents=True,exist_ok=True)
FONT=r'C:\Windows\Fonts\msyh.ttc'
F=lambda size:ImageFont.truetype(FONT,size)
pages={
'ready':('先选门的左下角',['用右手柄的射线，瞄准真实门框的左下角。','按右扳机：记录第一条线；再换个位置瞄准同一个角。','这里只显示现实房间；四点确认后才显示门和场景。']),
'no_saved':('暂时没有找到上次的位置',['按右扳机，从真实门框左下角开始重新定位。','如果上次位置正在恢复，可以稍后再按 Y 查看。','不会自动弹出门或场景。']),
'passthrough_wait':('正在开启现实画面，暂不能选点',['请等真实房间和门框出现在眼前，再开始定位。','系统会自动重试；仍无画面时请退出后重新打开。','当前没有记录点位；按 B 可以取消定位。']),
'intro':('手柄已就位，先选场景再定位',['A  切换：山景 / 平地花海','X  开始四点定位；B  收起 / 展开这张提示','右侧握把  开关门；Y  显示 / 隐藏虚拟门框']),
'step0':('第 1 / 4 点 · 左下角 · 第一线',['用右手柄射线瞄准门洞左下角。','按一次右扳机，先记下第一条线。','每个角点需要从两个不同位置，各瞄准一次。']),
'step1':('第 2 / 4 点 · 右下角 · 第一线',['用右手柄射线瞄准门洞右下角。','按一次右扳机，先记下第一条线。','手柄留在身前即可；按 B 取消定位。']),
'step2':('第 3 / 4 点 · 左上角 · 第一线',['用右手柄射线瞄准门洞左上角。','按一次右扳机，先记下第一条线。','不需要举到门顶，直接用射线瞄准。']),
'step3':('第 4 / 4 点 · 右上角 · 第一线',['用右手柄射线瞄准门洞右上角。','按一次右扳机，先记下第一条线。','这个角点完成两条线后，会显示门框预览。']),
'pair0':('第 1 / 4 点 · 左下角 · 第二线',['横向移动手柄 30–50 厘米，再瞄准同一个左下角。','蓝点和橙点是两线的最近点，短线越短越好。','不需要相交；调整到满意后，按右扳机记下中点。']),
'pair1':('第 2 / 4 点 · 右下角 · 第二线',['换个位置，再瞄准同一个右下角。','上方实时显示两线最近距离，单位是厘米。','没有 5 厘米门槛；位置满意就按右扳机。']),
'pair2':('第 3 / 4 点 · 左上角 · 第二线',['横向移动手柄 30–50 厘米，再瞄准同一个左上角。','蓝点和橙点之间的中间位置，就是将要记下的点。','尽量缩短两点间的连线，再按右扳机。']),
'pair3':('第 4 / 4 点 · 右上角 · 第二线',['横向移动手柄 30–50 厘米，再瞄准同一个右上角。','不用追求完全相交，调整最近点后按右扳机。','完成后检查现实门框上的细线，再按一次确认。']),
'preview':('四点已齐 · 先看门框是否对齐',['查看绿色轮廓是否贴住真实门洞的四个内角。','对齐了：松开扳机，再按一次右扳机确认。','不对：左扳机撤销上一条线；B 取消；X 全部重选。']),
'saved':('定位已确认，并已保存',['现在可以移动头部，观察门后山景 / 平地花海。','A 切换场景；右侧握把开关门；Y 切换门框显示。','X 重新定位；B 收起 / 展开提示。']),
'session':('本次可以使用，位置未能保存',['当前门的位置仍然有效，可以继续体验。','下次打开可能回到上次保存位置，请重新定位。','A 切换场景；X 重新定位；B 收起提示。']),
'busy':('正在准备或保存定位，请稍等',['保持头显开启，让摄像头看清周围环境。','如果弹出空间数据授权，请在头显里选择允许。','完成后会显示结果。']),
'locating':('正在寻找上次保存的门的位置',['缓慢环顾门框周围，让头显重新认出这个房间。','如果房间已改变或位置不对，按 X 重新定位。','按 B 可以收起这张提示。']),
'wait':('手柄跟踪暂停 · 点和线已保留',['现在显示的是暂停前的位置和距离，不会自动记录。','把右手柄放回头显摄像头看得到的位置。','恢复后继续调整；左扳机撤销；B 取消。']),
'ray_baseline':('换个位置，更容易看准远近',['第一条线已经保留。','横向移动一些，再瞄准同一个门框内角。','没有最小移动距离限制，也不会因此隐藏点。']),
'ray_parallel':('两线平行 · 距离仍在显示',['平行线有多个同样近的位置，暂沿用上次远近。','横向移动手柄，再瞄准同一个门框内角。','点和厘米数会保留；按右扳机仍可记录。']),
'ray_far':('最近点较远 · 仍在计算',['点在 8 米以外，距离没有被截断。','请把第二条线转回当前要选的真实门框内角。','数值持续更新；没有距离门槛，可手动确认。']),
'ray_origin':('最近点靠近手柄 · 仍在计算',['两条射线朝不同方向展开，最近位置就在起点附近。','转动第二条线，再瞄准第一线对应的门框内角。','点和距离持续显示；按右扳机仍可记录。']),
'ray_range':('当前手柄数据暂不可用',['已经保留最近一次的点和线，不会自动记录。','把右手柄放回头显摄像头看得到的位置。','跟踪恢复后继续调整；按 B 可以取消。']),
'error_duplicate':('这个角点和之前的点太近',['请确认两次瞄准的是当前提示的同一个内角。','左扳机撤销上一条线；X 可从头重新选择。','只记录门洞四个内角，不记录门板上的格子。']),
'error_width':('左右两个下角的距离不合适',['支持的门洞净宽是 0.35 到 3 米。','按 X 重新选择：左下 → 右下 → 左上 → 右上。','请检查绿色射线落点是否指在真实门框上。']),
'error_height':('上角和下角的高度不合适',['支持的门洞净高是 0.5 到 3.5 米。','按左扳机重选上一点，或按 X 从头选择。','上角要选在同一侧下角的正上方。']),
'error_order':('左右顺序或站的位置不对',['请站在准备观看的一侧，面对门洞。','按 X 重选：左下 → 右下 → 左上 → 右上。','定位期间先不要走到门的另一侧。']),
'error_shape':('四个点还没有围成同一个门洞',['上角应在下角正上方，两侧高度应接近。','左扳机撤销上一点；X 从头选择；B 取消。','请把射线瞄准门洞内角，避开后面的远处物体。']),
'mountain':('已切换 · 原始山坡场景',['保留原始起伏地形，花草随坡面排列。','门的位置保持不变，不用重新选择四个点。','再按 A，可回到平缓花海。']),
'flat':('已切换 · 平缓花海',['这是刚才正在体验的平缓地形。','门的位置保持不变，不用重新选择四个点。','再按 A，可切换原始山坡。']),
'frame_on':('虚拟门框 · 显示',['用于检查四个角是否和真实门框对齐。','再按 Y 隐藏虚拟门框外观，保留遮挡。','右侧握把可以开关虚拟门扇。']),
'frame_off':('虚拟门框 · 仅保留遮挡',['现在由真实门框提供外观。','再按 Y 恢复显示，方便检查位置。','右侧握把可以开关虚拟门扇。']),
'door_open':('虚拟门 · 已打开',['透过门洞观察另一侧的场景。','再次按右侧握把，可关上虚拟门。','A 切换场景；B 收起提示。']),
'door_closed':('虚拟门 · 已关上',['再次按右侧握把，可打开虚拟门。','真实门板仍由你亲手操作。','A 切换场景；B 收起提示。']),
'cancelled':('已取消定位，返回之前的位置',['刚才没有覆盖已保存的门的位置。','X 可重新开始；A 切换山景 / 平缓花海。','B 收起 / 展开提示。'])}
def glass(size):
    w,h=size;im=Image.new('RGBA',size);d=ImageDraw.Draw(im)
    for y in range(h):
        t=y/h;d.line((0,y,w,y),fill=(int(23-10*t),int(33-12*t),int(57-20*t),245))
    mask=Image.new('L',size);ImageDraw.Draw(mask).rounded_rectangle((2,2,w-3,h-3),radius=30,fill=245)
    im.putalpha(mask);d=ImageDraw.Draw(im)
    d.rounded_rectangle((2,2,w-3,h-3),radius=30,outline=(125,159,191,180),width=2)
    return im,d
def pill(d,box,label,color=(112,230,204),font=23):
    d.rounded_rectangle(box,radius=15,fill=(color[0]//5,color[1]//5,color[2]//5,255),outline=(*color,160),width=1)
    bounds=d.textbbox((0,0),label,font=F(font));tw=bounds[2]-bounds[0];th=bounds[3]-bounds[1]
    x0,y0,x1,y1=box;d.text(((x0+x1-tw)/2,(y0+y1-th)/2-bounds[1]),label,font=F(font),fill=color)
def keycap(d,x,y,label,color):
    d.rounded_rectangle((x,y,x+50,y+50),radius=16,fill=color)
    b=d.textbbox((0,0),label,font=F(29));d.text((x+(50-b[2])/2,y+5),label,font=F(29),fill=(14,25,40))
for key,(title,lines) in pages.items():
    im,d=glass((1200,420))
    accent=(255,206,118) if key.startswith(('step','error')) else (120,230,206)
    if key=='mountain':accent=(185,169,255)
    # Minimal door mark and brand, kept separate from the current task.
    d.rounded_rectangle((40,28,63,59),radius=4,outline=accent,width=2);d.line((47,57,47,33,61,28),fill=accent,width=2)
    d.text((77,25),'梦幻门',font=F(25),fill=(203,219,234))
    d.text((182,29),'手柄指南',font=F(20),fill=(133,157,182))
    chip='第 1 条线' if key.startswith('step') else ('第 2 条线' if key.startswith('pair') else {'busy':'请稍等','preview':'等待确认','saved':'位置已保存','session':'本次有效','wait':'等待手柄','locating':'识别房间'}.get(key,'手柄操作'))
    pill(d,(1015,24,1155,66),chip,accent,21)
    d.text((42,84),title if key!='intro' else '把另一片世界，放进你的门。',font=F(42),fill=(241,247,255))
    d.line((44,145,1155,145),fill=(63,84,111,200),width=1)
    diagram=key.startswith(('step','pair')) or key=='preview'
    if key=='intro':
        tiles=[('A','场景切换','平缓花海 / 原始山坡',(118,226,193)),('X','双射线四点定位','每个角换个位置，瞄准两次',(136,191,255)),('握','开门 / 关门','按右侧握把，切换门的状态',(201,178,255)),('B','收起 / 展开提示','留出视野，专心看风景',(255,188,169))]
        for i,(button,name,desc,color) in enumerate(tiles):
            x=42+(i%2)*564;y=166+(i//2)*106
            d.rounded_rectangle((x,y,x+545,y+91),radius=17,fill=(32,46,69,220),outline=(58,80,106,200),width=1)
            keycap(d,x+18,y+20,button,color)
            d.text((x+87,y+12),name,font=F(29),fill=(239,246,255))
            d.text((x+87,y+53),desc,font=F(22),fill=(167,192,212))
    else:
        font=F(28 if diagram else 30)
        for i,line in enumerate(lines):d.text((44,173+i*61),line,font=font,fill=(220,233,245) if i else (247,251,255))
    if diagram:
        d.rounded_rectangle((937,166,1155,353),radius=18,fill=(17,29,45,255),outline=(67,95,119),width=1)
        x0,x1,y0,y1=978,1114,198,321
        d.rectangle((x0,y0,x1,y1),outline=(100,139,162),width=4)
        current=int(key[-1]) if key.startswith(('step','pair')) else 4
        for i,(x,y) in enumerate(((x0,y1),(x1,y1),(x0,y0),(x1,y0))):
            color=accent if i==current else ((120,230,206) if i<current else (79,105,130))
            if i==current:d.ellipse((x-29,y-29,x+29,y+29),outline=(*accent,200),width=2)
            d.ellipse((x-20,y-20,x+20,y+20),fill=color)
            d.text((x-8,y-17),str(i+1),font=F(25),fill=(13,25,40))
    if diagram or key.startswith('error'):
        d.text((44,380),'同一个角，两条线  ·  右扳机记录  ·  左扳机撤销一条线',font=F(19),fill=(132,158,179))
    im.save(OUT/(key+'.png'))
for mode,label in [('flat','平缓花海'),('mountain','原始山坡')]:
    im,d=glass((1200,108));accent=(120,230,206) if mode=='flat' else (191,173,255)
    pill(d,(18,16,206,65),label,accent,26)
    for i,(button,name,color) in enumerate([('A','换场景',(118,226,193)),('X','定位',(136,191,255)),('B','帮助 / 取消',(255,188,169)),('Y','门框',(255,213,138))]):
        x=235+i*237
        d.rounded_rectangle((x,17,x+35,52),radius=10,fill=color);d.text((x+7,19),button,font=F(23),fill=(14,25,40))
        d.text((x+46,19),name,font=F(25),fill=(227,240,249))
    d.text((235,71),'右扳机 记录射线 / 确认    左扳机 撤销    右握把 开关门',font=F(22),fill=(155,182,204))
    im.save(OUT/('footer_'+mode+'.png'))
    for context,commands,detail in [
        ('ready','右扳机  开始选点    X  重选    Y  上次位置','A 可先选场景；完成四点并确认后才显示。'),
        ('placement','右扳机  记线 / 记点    左扳机  撤回    B  取消','X  从头重选；A 只选择之后的场景，不打断定位。')]:
        im,d=glass((1200,108));pill(d,(18,16,206,65),label,accent,26)
        d.text((235,18),commands,font=F(25),fill=(227,240,249))
        d.text((235,70),detail,font=F(22),fill=(155,182,204))
        im.save(OUT/('footer_'+context+'_'+mode+'.png'))
for key,(title,lines) in pages.items():
    im,d=glass((1200,248));accent=(120,230,206)
    d.text((34,17),title,font=F(38),fill=(241,247,255))
    d.line((34,72,1165,72),fill=(63,84,111,200),width=1)
    for i,line in enumerate(lines):
        d.text((34,88+i*49),line,font=F(30 if i<2 else 25),fill=(233,243,250) if i<2 else (164,188,207))
    im.save(OUT/('compact_'+key+'.png'))
im,d=glass((640,104))
d.text((24,23),'两线相差',font=F(38),fill=(221,235,246))
d.text((555,27),'cm',font=F(34),fill=(174,197,217))
im.save(OUT/'gap_label.png')
im=Image.new('RGBA',(11*64,96));d=ImageDraw.Draw(im)
digit_metrics=d.textbbox((0,0),'0123456789',font=F(64))
digit_y=(96-(digit_metrics[3]-digit_metrics[1]))/2-digit_metrics[1]
for i,c in enumerate('0123456789.'):
    b=d.textbbox((0,0),c,font=F(64));d.text((i*64+(64-(b[2]-b[0]))/2-b[0],digit_y),c,font=F(64),fill=(255,255,255))
im.save(OUT/'gap_digits.png')
# Match the known readable FBX importer used for the existing terrain.
meta=(ROOT/'Assets/Models/DreamWorld.fbx.meta').read_text(encoding='utf-8')
meta=meta.replace('5664d0a2cc282d34cbaa132d6e3eaf74',uuid.uuid4().hex)
target=ROOT/'Assets/Resources/Worlds/MountainWorld.fbx.meta'
if not target.exists(): target.write_text(meta,encoding='utf-8')
print(f'Generated {len(pages)+2} controller instruction textures')
