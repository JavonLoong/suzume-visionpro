from pathlib import Path
import json,numpy as np,cv2
from PIL import Image,ImageDraw
from scipy.ndimage import map_coordinates
from scipy.optimize import differential_evolution
R=Path(__file__).parent;O=R/'poster-right-arches-v55';im=np.asarray(Image.open('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103/reference-hires.jpg').convert('RGB'));gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY).astype(float)/255;theta=np.linspace(.15,np.pi-.15,96)
manual=[[532.8,8.3,585.4,6.0,599.4],[551.06,7.44,585.0,5.7,598.5],[569.46,8.87,583.8,5.96,597.4],[586.95,9.03,582.5,6.28,596.2],[605.5,8.4,580.8,6.3,595.0],[622.3,8.5,579.1,6.3,593.8],[641.0,8.4,578.9,5.9,592.5],[660,8.7,576.8,6.3,591.2],[679.3,9.3,575.6,6.3,589.9],[699.8,10.0,574.2,6.7,588.5]];out=[]
def path(p):
 u=p[0]+p[1]*np.cos(theta);v=p[2]+p[3]*(1-np.sin(theta))-.04*(u-p[0]);return u,v
for i,row in enumerate(manual):
 initial=np.array(row[:4]);bounds=[(initial[j]-delta,initial[j]+delta) for j,delta in enumerate([.7,.7,.6,1.0])]
 def score(p):
  u,v=path(p);normal=np.array([np.cos(theta)/p[1],-np.sin(theta)/p[3]]);normal/=np.linalg.norm(normal,axis=0);values=[]
  for off in [-.95,0,.95]:values.append(map_coordinates(gray,[(v+normal[1]*off)*2.824,(u+normal[0]*off)*2000/708],order=1,mode='nearest'))
  return float(np.mean(values[1]-(values[0]+values[2])*.5)+.006*np.mean(((np.array(p)-initial)/[.7,.7,.6,1.0])**2))
 fit=differential_evolution(score,bounds,seed=55055+i,popsize=7,maxiter=65,polish=True).x;out.append({'id':i,'manual':row,'fitted':[round(float(x),4) for x in fit]+[row[4]],'manualScore':score(initial),'fitScore':score(fit),'baseEvidence':'Measured/inferred continuation behind foreground beam; not the occluding steel contour.'})
q=Image.fromarray(im).crop((520*2000/708,565*2.824,2000,607*2.824)).resize((1128,252));c=Image.new('RGB',(1128,277),(20,20,20));c.paste(q,(0,25));d=ImageDraw.Draw(c)
for row in out:
 p=row['fitted'];u,v=path(p);d.line(list(zip((u-520)*6,(v-565)*6+25)),fill=(255,60,180),width=1);d.text(((p[0]-520)*6-8,(p[2]-565)*6+10),str(row['id']),fill=(0,255,80))
for x in range(525,708,10):d.text(((x-520)*6,2),str(x),fill='white')
c.save(O/'arch-cap-fit-v55.png');(O/'arch-cap-measurements-v55.json').write_text(json.dumps(out,indent=2));print('RIGHT_ARCHES_55_CAP_FITS',[(q['id'],q['fitted']) for q in out])
