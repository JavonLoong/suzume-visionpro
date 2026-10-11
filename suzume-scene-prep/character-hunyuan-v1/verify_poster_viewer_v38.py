from pathlib import Path
import hashlib,json,re,subprocess,urllib.request
R=Path(__file__).parent;O=R/'poster-v38';p=R/'viewer/poster-v38.html';s=p.read_text(encoding='utf-8')
assert "let state={open:false,motion:false,azimuth:posterComposition.azimuth" in s
assert 'suzume-poster-view-v38' in s
assert 'character-v37/suzume-posed-v37.gltf' in s
assert 'makeDoorLeafRigid32(T,hinge);makeDoorLeafRigid32(T,nightHinge);' in s
assert 'applyMovieTerrain31' not in s and 'applyMovieNight30' not in s
assert 'candidate-v37.html' in s and '../poster-v38/Suzume_dual_scene_v38.blend' in s
scripts=[]
for i,(attributes,body) in enumerate(re.findall(r'<script\b([^>]*)>(.*?)</script>',s,re.S)):
    if not body.strip():continue
    q=O/f'poster-script-{i}-v38.js';q.write_text(body,encoding='utf-8');subprocess.run(['C:/Program Files/nodejs/node.exe','--check',str(q)],check=True,capture_output=True);scripts.append(q.name)
files=['viewer/poster-v38.html','viewer/three.min.js','viewer/GLTFLoader.js','viewer/character-v37/suzume-posed-v37.gltf','poster-v38/Suzume_dual_scene_v38.blend']
doc=json.loads((R/files[3]).read_text(encoding='utf-8'))
files+=['viewer/character-v37/'+x['uri'] for x in doc.get('buffers',[])+doc.get('images',[]) if x.get('uri') and not x['uri'].startswith('data:')]
checks=[]
for name in dict.fromkeys(files):
    with urllib.request.urlopen('http://127.0.0.1:8931/'+name,timeout=20) as response:
        digest=hashlib.sha256(response.read()).hexdigest()
    assert digest==hashlib.sha256((R/name).read_bytes()).hexdigest(),name
    checks.append({'path':name,'sha256':digest})
report={'revision':38,'initialView':'closed poster','independentStorageKey':True,'latestCharacterAssetRevision':37,'rigidDoorPreserved':True,'movieEnvironmentMutationsExcluded':True,'inlineScriptsParsed':scripts,'httpResources':checks,'browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'browser-verification-v38.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('POSTER_BROWSER_RESOURCES_VERIFIED',len(checks),'GPU_RENDER_UNVERIFIED')
