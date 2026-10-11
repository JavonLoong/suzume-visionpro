from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,zipfile
R=Path(__file__).parent
checks={}
for view in ['front','left','back','right']:
 p=R/f'{view}.png';im=Image.open(p).convert('RGB');a=np.array(im);mask=a.min(axis=2)<225;ys,xs=np.where(mask)
 checks[view]={'file':p.name,'dimensions':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'foregroundBounds':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]}
status={'stage':'four_views_and_attachment_ready_browser_unresponsive','headModelSubmitted':False,'headModelGenerated':False,'headModelIntegrated':False,'hunyuanSubmissionsThisStage':0,'imageTool':'built-in image_gen','imageGenerationCalls':6,'views':checks,'prompts':'prompts.json','attachmentGuide':'attachment-guide.json','attachmentFile':'head-socket-preparation.blend','attachmentNote':'Contains the extracted ORIGINAL head as an alignment reference; it is not the requested newly generated head.','viewConsistency':'Asymmetric left-only pins and centered ponytail visually checked. Side/front face landmark heights still vary; inspect model against official film references.','browserBlocker':'New IAB tabs did not finish navigation; existing tab also stopped responding to CDP/DOM. App open commands queued; user confirmed page still absent. No cloud generation was submitted.','oneToOneComplete':False}
(R/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'使用说明.txt').write_text('独立头部重建输入\n\nfront.png：正面。left.png：人物左侧，能看见金色发卡与红色交叉发卡。right.png：人物右侧，无发卡。back.png：背面，马尾居中。\n图像由内置 image_gen 根据电影参照生成，不是官方正交设定图；完整提示词见 prompts.json。\n\n目前尚未提交混元，尚未生成或替换新头模。浏览器连接无响应，已保存四视图等待恢复。\nhead-socket-preparation.blend 是旧模型头部拆分与衣领接合准备，不是新头模。\n接入时先检查新头模正脸、两侧和发卡，再拟合 attachment-guide.json 中的脖颈位置，保留 v16 的脚部碰撞修复与庭院/异世界裁分。\n',encoding='utf-8')
with zipfile.ZipFile(R/'Suzume-head-multiview-inputs.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for name in ['front.png','left.png','back.png','right.png','prompts.json','status.json','attachment-guide.json','使用说明.txt']:archive.write(R/name,name)
main=R.parent/'status.json';s=json.loads(main.read_text(encoding='utf-8'));s['scene']['headReconstruction']='Four views and reversible neck attachment prepared; cloud generation not submitted because browser is unresponsive.';s['headReconstructionAudit']='head-hunyuan-v1/status.json';main.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print('HEAD_INPUTS_PACKAGED',json.dumps(checks),flush=True)
