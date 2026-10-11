"""Expose the inspected alternate without replacing the Hunyuan v17 default."""
from pathlib import Path
import json,re,subprocess,hashlib,urllib.request
R=Path(__file__).parent;H=R/'head-hunyuan-v1';O=H/'clean-v18';W=R/'viewer'
checks=json.loads((H/'verification-v18.json').read_text(encoding='utf-8'))
native=json.loads((H/'native-integration-v18.json').read_text(encoding='utf-8'))
assert checks['bodyAndFootWorldVerticesExactlyPreserved'] and checks['backRender']
assert native['nativeRenderVerified']
assert (R/'native-pose-back-v18.png').is_file()
gltf=json.loads((W/'suzume-posed-v18.gltf').read_text(encoding='utf-8'))
triangles=sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])
assert triangles==544593,triangles
assert len(gltf['meshes'])==2
assert len(gltf['meshes'][1]['primitives'])==12
resources=[]
for section in ('buffers','images'):
    for row in gltf.get(section,[]):
        if 'uri' in row and not row['uri'].startswith('data:'):
            assert (W/row['uri']).is_file(),row['uri'];resources.append(row['uri'])
web=[]
for page in ['index.html','candidate-v18.html']:
    html=(W/page).read_text(encoding='utf-8')
    assert 'value="head"' in html and 'localClippingEnabled=true' in html
    blocks=[block for attrs,block in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S) if 'src=' not in attrs and block.strip()]
    for i,block in enumerate(blocks):
        result=subprocess.run(['C:/Program Files/nodejs/node.exe','--check','-'],input=block,text=True,capture_output=True)
        assert result.returncode==0,result.stderr
    with urllib.request.urlopen('http://127.0.0.1:8931/viewer/'+page,timeout=10) as response:
        payload=response.read();assert response.status==200
        assert hashlib.sha256(payload).digest()==hashlib.sha256((W/page).read_bytes()).digest()
    web.append({'page':page,'syntaxChecked':True,'servedBytesMatch':True})
audit=json.loads((O/'candidate-audit.json').read_text(encoding='utf-8'))
audit.update(status='integrated_alternate_available',nativeVerification='../verification-v18.json',
             visualReview={'views':['front','left','back','threequarter','posed-front','posed-head','posed-head-side','native-front','native-back'],
                           'improvements':['Hairpins conform to the outer hair surface.','Smooth crown and volumetric ponytail.','Clean separate eye geometry.','Closed jaw and continuous neck connection.'],
                           'limitations':['Facial identity and expression remain approximate.','Hair silhouette and ear detail still differ from the film.','Not promoted over the Hunyuan v17 default.']})
(O/'candidate-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
release={'revision':18,'role':'alternate_clean_mathematical_head','defaultSceneRevision':17,
         'headProvenance':'Mathematical reconstruction from film references; Hunyuan v17 registration only. No new cloud generation.',
         'fullScene':'../Suzume_scene_clean_head_v18.blend','character':'../Suzume_character_head_v18.blend',
         'sourceParts':'clean-v18/Suzume-clean-head-v18.blend','viewer':'../viewer/candidate-v18.html',
         'nativeFrontAndBackVerified':True,'bodyAndFeetExactlyPreserved':True,'browserTriangles':triangles,
         'browserMaterialRegions':13,'localResources':resources,'webStaticChecks':web,
         'browserRuntimeVerified':False,'browserLimitation':'In-app browser control still timed out. No runtime claim is made.',
         'oneToOneComplete':False}
(H/'release-v18.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
for path in [H/'status.json',R/'status.json']:
    status=json.loads(path.read_text(encoding='utf-8'))
    status['alternateHeadCandidate']={'revision':18,'method':'Reference-driven mathematical head; not a new Hunyuan generation',
                                     'viewer':'viewer/candidate-v18.html' if path.parent==R else '../viewer/candidate-v18.html',
                                     'defaultStillV17':True,'nativeVerified':True,'browserRuntimeVerified':False,
                                     'oneToOneComplete':False}
    path.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
gallery=(R/'index.html').read_text(encoding='utf-8')
section='''<section id="clean-head-v18"><h2>几何头部对比版 · v18</h2>
<p>在保留混元身体的基础上，按参照重新构造脸部、眼睛、发束和发卡。它是数学建模对比版，不是再次调用混元生成。脸部神态仍需校准，原混元头模版本继续保留。</p>
<p><a href="viewer/candidate-v18.html">打开可旋转对比场景</a>（视角可选“人物近景”） · <a href="Suzume_scene_clean_head_v18.blend">完整 Blender 场景</a> · <a href="head-hunyuan-v1/clean-v18/Suzume-clean-head-v18.blend">分部件头模源文件</a> · <a href="viewer/suzume-posed-v18.glb">人物 GLB</a></p>
<div class="views"><figure><img src="head-hunyuan-v1/clean-v18/head-front.png" alt="几何头模正面"><figcaption>正面</figcaption></figure><figure><img src="head-hunyuan-v1/clean-v18/head-left.png" alt="几何头模侧面"><figcaption>侧面</figcaption></figure><figure><img src="head-hunyuan-v1/clean-v18/head-back.png" alt="几何头模背面"><figcaption>背面</figcaption></figure><figure><img src="head-hunyuan-v1/clean-v18/head-threequarter.png" alt="几何头模斜侧面"><figcaption>斜侧面</figcaption></figure></div>
<p>原生场景正反面已验证，脚部与身体顶点保持不变。浏览器连接仍超时，新增网页交互待复测。<a href="head-hunyuan-v1/release-v18.json">验证记录</a></p></section>'''
if '<section id="clean-head-v18">' in gallery:
    gallery=re.sub(r'<section id="clean-head-v18">.*?</section>',section,gallery,flags=re.S)
else:gallery=gallery.replace('<h2>新头部的四视图输入</h2>',section+'<h2>新头部的四视图输入</h2>')
(R/'index.html').write_text(gallery,encoding='utf-8')
(O/'使用说明.txt').write_text('''几何头部对比版 v18

这是按电影参照构造的可编辑几何头模，不是新的混元生成结果。
Suzume-clean-head-v18.blend 保留 58 个分部件；已导出独立 GLB。
完整场景：上两级目录 Suzume_scene_clean_head_v18.blend。
可旋转对比： http://127.0.0.1:8931/viewer/candidate-v18.html
网页视角可选择“人物近景”，检查眼睛、头发与颈部。

原混元身体、20 骨骼、v16 脚部修复和门两侧分隔均已保留。
原生正反面验证通过；浏览器运行时仍未复测。
脸部神态、发型轮廓和耳朵细节仍是近似，尚未一比一。
默认场景继续使用 v17 混元独立头模。
''',encoding='utf-8')
print(json.dumps(release,ensure_ascii=False,indent=2))
