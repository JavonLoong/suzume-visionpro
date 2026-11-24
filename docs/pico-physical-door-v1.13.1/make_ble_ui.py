from pathlib import Path
import uuid,re
from PIL import Image,ImageDraw,ImageFont
r=Path('D:/suzume-picounity/Assets/Resources/ControllerGuide')
meta=(r/'slim_ready.png.meta').read_text(encoding='utf8')
titles={'ready':'主控已连接，可以开门','opened':'主控已确认：开门到位','closed':'主控已确认：复位到位','opening':'正在开门，等待到位回复','closing':'正在复位，等待到位回复','sending':'指令已发出，等待主控确认','query':'主控已连接，正在读取状态','scanning':'正在寻找实体门主控','connecting':'正在连接实体门主控','permission':'请允许“附近设备”蓝牙权限','UNCAL':'主控尚未标定，暂不能动作','READ':'主控读不到位置，暂不能动作','POSITION':'未到目标位置，请检查机构','UART':'主控未能下发舵机指令','bluetooth_off':'请开启头显蓝牙','scan_timeout':'没找到主控，请确认已通电','disconnected':'连接已断开或超时，正在重连'}
previews=[]
for key,title in titles.items():
 subtitle='右 A 开门  ·  右 B 复位  ·  左 X 定位  ·  按右摇杆微调' if key in {'ready','opened','closed'} else '请等状态恢复后再操作  ·  左 X 定位  ·  按右摇杆微调'
 if key in {'scanning','connecting','scan_timeout','disconnected'}:subtitle='连接后先读取状态，不会自动开门或复位  ·  左 X 定位'
 im=Image.new('RGBA',(1200,180));d=ImageDraw.Draw(im);d.rounded_rectangle((2,2,1197,177),radius=36,fill=(17,23,31,235),outline=(112,135,153,100),width=2)
 color=(115,226,177) if key in {'ready','opened','closed'} else (255,194,106)
 d.ellipse((34,44,48,58),fill=color)
 for text,y,size in [(title,22,44),(subtitle,101,29)]:
  while True:
   font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)
   if d.textbbox((0,0),text,font=font)[2]<=1090:break
   size-=1
  d.text((72,y),text,font=font,fill=(244,247,250) if y==22 else (177,192,204))
 p=r/f'slim_ble_{key}.png';im.save(p)
 if not p.with_suffix('.png.meta').exists():p.with_suffix('.png.meta').write_text(re.sub(r'guid: \w+','guid: '+uuid.uuid4().hex,meta),encoding='utf8')
 if key in {'ready','opening','opened','scan_timeout'}:previews.append(im)
canvas=Image.new('RGB',(1200,len(previews)*200),(39,45,51))
for i,im in enumerate(previews):canvas.paste(im,(0,i*200),im)
canvas.save(Path(__file__).parent/'ble-ui-preview.png')
print('BLE guide cards:',len(titles))
