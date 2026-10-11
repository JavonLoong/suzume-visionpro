from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;O=R/'poster-steel-v39';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
D=json.loads((O/'steel-geometry-v39.json').read_text());cal=json.loads((V/'dome-calibration-v7.json').read_text());M=np.array(D['camera']['matrixWorld']);C=M[:3,3];f=D['camera']['lens']/36*2824
def project(p):
    q=(np.asarray(p)-C)@M[:3,:3];return np.c_[1000+f*q[:,0]/-q[:,2],1412-f*q[:,1]/-q[:,2]]
def distances(points,path):
    a=path[:-1];d=np.diff(path,axis=0);delta=points[:,None,:]-a;u=np.clip(np.sum(delta*d,axis=2)/np.maximum(np.sum(d*d,axis=1),1e-12),0,1)
    return np.min(np.linalg.norm(delta-u[:,:,None]*d,axis=2),axis=1)
rows=[]
for index in [2,3]:
    q=next(q for q in D['members'] if q.get('ribIndex')==index);observed=np.array(q['referencePixels']);angle=cal['angles'][index];t=np.linspace(0,cal['ends'][index],1000);top=np.c_[20.3*np.sin(angle)*np.cos(t),20.3*np.cos(angle)*np.cos(t),5.75+12*np.sin(t)];bottom=np.array([[20.3*np.sin(angle),20.3*np.cos(angle),.54]])
    before=distances(observed,project(np.vstack([bottom,top])));after=distances(observed,project(q['centerlineNative']))
    rows.append({'ribIndex':index,'referencePixels':q['referencePixels'],'oldCenterlineErrorsPixels':before.tolist(),'newCenterlineErrorsPixels':after.tolist(),'oldMean':float(before.mean()),'oldMaximum':float(before.max()),'newMean':float(after.mean()),'newMaximum':float(after.max())})
report={'revision':39,'referenceDimensions':[2000,2824],'measurementUncertaintyPixels':4,'columns':rows,'scope':'Distance from manually selected column-center observations to projected modeled centerlines. Not a silhouette-width, material, depth or whole-scene equivalence test.','oneToOneComplete':False}
(O/'projection-comparison-v39.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps([{k:r[k] for k in ['ribIndex','oldMean','oldMaximum','newMean','newMaximum']} for r in rows],indent=2))
