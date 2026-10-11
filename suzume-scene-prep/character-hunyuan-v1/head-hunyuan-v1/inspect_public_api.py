from pathlib import Path
import sys, os, json
H = Path(__file__).parent
sys.path.insert(0, str(H / 'python-deps'))
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
from gradio_client import Client
client = Client('https://tencent-hunyuan3d-2mv.hf.space', token=False,
                httpx_kwargs={'timeout': 30}, analytics_enabled=False,
                download_files=str(H / 'public-api-output'))
schema = client.view_api(return_format='dict', print_info=False)
(H / 'public-api-schema.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding='utf-8')
for name, api in schema['named_endpoints'].items():
    if 'generation' in name:
        print(name, json.dumps(api, ensure_ascii=False), flush=True)
