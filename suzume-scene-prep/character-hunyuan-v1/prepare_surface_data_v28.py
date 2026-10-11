"""Mathematical color LUT and geometric visibility mask; source photo stays unmodified."""
from pathlib import Path
import json,sys,hashlib,shutil,numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).parent;O=R/'movie-surfaces-v28';O.mkdir(exist_ok=True);sys.path.insert(0,str(R/'color-pipeline-deps'));import PyOpenColorIO as ocio
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
source=V/'reference-opening-50525.jpg';shutil.copy2(source,O/'reference-opening.jpg')
P=json.loads((R/'movie-projection-v24/joint-fit-v24.json').read_text())['parameters'];steel=json.loads((R/'movie-steel-v25/steel-fit-v25.json').read_text())
polygons=[
 {'name':'door and character','points':[[904,206],[1568,205],[1574,1512],[892,1512]]},
 {'name':'ivy above the door','points':[[1170,231],[1200,201],[1280,188],[1385,161],[1465,174],[1532,220],[1569,327],[1470,290],[1435,246],[1310,246]]},
 {'name':'left column and climbing ivy','points':[[389,0],[446,0],[445,340],[480,393],[463,655],[474,840],[389,861],[390,486],[361,354],[385,323]]},
 {'name':'right column and climbing ivy','points':[[1835,0],[1899,0],[1895,482],[1930,560],[1910,846],[1820,846],[1814,559],[1833,475]]}
]
mask=Image.new('L',(2552,1656),255);draw=ImageDraw.Draw(mask)
top=[[0,0],[1835,0],[1912,270],[2552,241]]
draw.polygon([[0,0],[2552,0],*list(reversed(top))],fill=0)
draw.rectangle((0,694,2552,1656),fill=0)
for p in polygons:draw.polygon([tuple(q) for q in p['points']],fill=0)
for beam in steel['bowedBeams']:
    pts=[tuple(q) for q in beam['referencePixels']];draw.line(pts,fill=0,width=30,joint='curve')
    for x,y in pts:draw.ellipse((x-15,y-15,x+15,y+15),fill=0)
for q in steel['slenderTies']:
    x,y=q['referenceBottom'];draw.rectangle((x-8,0,x+8,y+9),fill=0)
# Vivid projected leaves should remain independent modeled plants, not foliage
# painted twice onto the plaster. Muted moss and staining are retained.
rgb=np.asarray(Image.open(source).convert('RGB'),dtype=float)/255
leaf=(rgb[:,:,1]>rgb[:,:,0]*1.05)&(rgb[:,:,1]>rgb[:,:,2]*1.15)&((rgb.max(2)-rgb.min(2))>.20)
leafMask=Image.fromarray((~leaf).astype('uint8')*255).filter(ImageFilter.MinFilter(7))
mask=Image.fromarray(np.minimum(np.asarray(mask),np.asarray(leafMask))).filter(ImageFilter.GaussianBlur(1.25));mask.save(O/'surface-validity-mask-v28.png')
config=Path('C:/Program Files/Blender Foundation/Blender 5.0/5.0/datafiles/colormanagement/config.ocio');cfg=ocio.Config.CreateFromFile(str(config))
inverse=cfg.getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_INVERSE).getDefaultCPUProcessor();forward=cfg.getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_FORWARD).getDefaultCPUProcessor()
n=65;axis=np.linspace(0,1,n,dtype='f4');g,b,r=np.meshgrid(axis,axis,axis,indexing='ij');lut=np.stack([r,g,b],axis=-1).reshape(n,n*n,3).copy();inverse.applyRGB(lut);lut/=2**.8
rgba=np.ones((n,n*n,4),dtype='f4');rgba[:,:,:3]=lut;np.save(O/'inverse-agx-lut-v28.npy',rgba)
# Validate trilinear interpolation on colors actually used by the unmodified
# image. This checks only the color table, not geometric or scene fidelity.
samples=rgb[::7,::7][np.asarray(mask)[::7,::7]>250].astype('f4');scaled=samples*(n-1);low=np.floor(scaled).astype(int);high=np.minimum(low+1,n-1);t=scaled-low
out=np.zeros_like(samples)
for dg in [0,1]:
 for db in [0,1]:
  for dr in [0,1]:
   rr=np.where(dr,high[:,0],low[:,0]);gg=np.where(dg,high[:,1],low[:,1]);bb=np.where(db,high[:,2],low[:,2]);w=(t[:,0] if dr else 1-t[:,0])*(t[:,1] if dg else 1-t[:,1])*(t[:,2] if db else 1-t[:,2]);out+=lut[gg,bb*n+rr]*w[:,None]
out*=2**.8;forward.applyRGB(out);err=np.max(np.abs(out-samples),axis=1)*255
spec={'revision':28,'sourceImage':'reference-opening.jpg','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceDimensions':[2552,1656],'sourceImageUnmodified':True,'projection':P,'maskPolygons':polygons,'topProfile':top,'bottomPixel':694,'beamMaskWidth':30,'vividLeafMask':True,'lutSize':n,'lutAtlasDimensions':[n*n,n],'lutExposure':.8,'lutConfigSha256':hashlib.sha256(config.read_bytes()).hexdigest(),'lutSignedValuesPreserved':True,'eligibleFrontDepth':[-.35,.8],'eligibleHeight':[1.55,8.4],'facingMinimum':.6,'nativeLeftMaterials':['material-0','material-1','material-2','material-6'],'oneToOneComplete':False,'limitations':['Reference shading is retained in surface pigments; these are not measured reflectance values.','Foreground occluders, vivid leaves and unobserved areas are excluded; their underlying surfaces remain inferred.','Only real front-facing plaster and stone surfaces are eligible, not new image planes.']}
(O/'surface-spec-v28.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8');audit={'sampleCount':len(samples),'medianMaxChannelError255':float(np.median(err)),'p99MaxChannelError255':float(np.percentile(err,99)),'maxChannelError255':float(err.max()),'scope':'Inverse display LUT interpolation on sampled valid reference colors only; not scene fidelity.'};(O/'lut-verification-v28.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print(json.dumps(audit,indent=2))
