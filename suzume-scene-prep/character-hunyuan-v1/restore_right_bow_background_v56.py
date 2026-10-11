from pathlib import Path
import json,hashlib,numpy as np,cv2
from scipy.interpolate import PchipInterpolator
from PIL import Image
R=Path(__file__).parent;O=R/'poster-right-bow-v56';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=json.loads((O/'right-bow-geometry-v56.json').read_text());points=np.array(D['boundaryObservations708']);bottom=PchipInterpolator(points[:,0],points[:,1],extrapolate=True);width=PchipInterpolator([523,550,580,610,640,670,700,712],[3.3,3.3,3.6,3.6,3.25,3.3,3.35,3.35],extrapolate=True)
src=np.asarray(Image.open(V/'reference-hires.jpg').convert('RGB'))[1410:2010];fit=np.array(json.loads((R/'poster-right-facade-v54/surface-restoration-v54.json').read_text())['sourceBGRToGradedBGRMatrix']);graded=np.rint(np.clip(np.c_[src[:,:,::-1].reshape(-1,3)/255,np.ones(600*2000)]@fit,0,1).reshape(600,2000,3)[:,:,::-1]*255).astype('u1')
yy,xx=np.indices((600,2000));u=xx*708/2000;v=(yy+1410)/2.824
region=(u>=532)&(v>=570)&(v<=625)
hidden=region&(v>=bottom(u)-width(u)-.3)&(v<=bottom(u)+.3)
oldmask=np.asarray(Image.open(V/'facade-exclusion-mask-v9.png').convert('L'))>0
patch=(oldmask&region)|hidden;observed=patch&~hidden
# Only the true narrow occluded strip is inpainted. All observable pixels in
# the obsolete broad exclusion are restored directly from the reference.
filled=cv2.inpaint(graded,(hidden*255).astype('u1'),3,cv2.INPAINT_NS)
rows=[]
for name,oldfile,newfile,image_name,browser_target in [
 ('Poster restored right facade pigments v54','poster-right-facade-v54/right-facade-pigments-v54.png','right-facade-beam-mask-v56.png','Right facade narrow beam mask v56','Poster right arcade prior54_0 v55'),
 ('Poster calibrated right arcade pigments v55','poster-right-arches-v55/right-arcade-pigments-v55.png','right-arcade-beam-mask-v56.png','Right arcade narrow beam mask v56','Poster right arcade new0 v55')]:
 prior=np.asarray(Image.open(R/oldfile).convert('RGB'));pixels=prior.copy();pixels[observed]=graded[observed];pixels[hidden]=filled[hidden];assert np.array_equal(pixels[~patch],prior[~patch]);assert np.array_equal(pixels[observed],graded[observed]);Image.fromarray(pixels).save(O/newfile)
 rows.append({'material':name,'previousAtlas':oldfile,'previousAtlasSha256':sha(R/oldfile),'newAtlas':newfile,'newImageName':image_name,'atlasSha256':sha(O/newfile),'browserTarget':browser_target,'observedPixelsRestored':int(observed.sum()),'hiddenPixelsInferred':int(hidden.sum()),'outsidePatchPreservedExactly':True,'observedPixelsEqualGradedSourceExactly':True})
(O/'surface-restoration-v56.json').write_text(json.dumps({'revision':56,'region708':[532,570,708,625],'actualBeamMaskMarginPixels':.3,'hiddenFill':'OpenCV Navier-Stokes inpainting, radius 3 source pixels. Hidden appearance is inferred.','surfaces':rows},indent=2),encoding='utf-8')
print('RIGHT_BOW_BACKGROUND_56_RESTORED',int(observed.sum()),int(hidden.sum()))
