"""One explicit four-view submission to Tencent's public Gradio endpoint."""
from pathlib import Path
import sys, os, json, time, traceback
from datetime import datetime, timezone
H = Path(__file__).parent
sys.path.insert(0, str(H / 'python-deps'))
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
from gradio_client import Client, handle_file
shape_only = '--shape-only' in sys.argv
attempt = 2 if shape_only else 1
api_name = '/shape_generation' if shape_only else '/generation_all'
record = H / f'public-generation-attempt-{attempt}.json'
if record.exists():
    raise SystemExit('Attempt already recorded. Inspect its outcome before any further submission.')
state = {'provider': 'Tencent official Hunyuan3D-2mv public Space',
         'url': 'https://huggingface.co/spaces/tencent/Hunyuan3D-2mv',
         'api': api_name, 'model': '2mv Turbo',
         'inputs': ['front.png', 'back.png', 'left.png', 'right.png'],
         'steps': 10, 'octree_resolution': 384, 'seed': 901010,
         'stage': 'connecting', 'startedAt': datetime.now(timezone.utc).isoformat(),
         'commercialWebsite31Submitted': False, 'modelGenerated': False}
def save():
    record.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
save()
try:
    client = Client('https://tencent-hunyuan3d-2mv.hf.space', token=False,
                    httpx_kwargs={'timeout': 60}, analytics_enabled=False,
                    download_files=str(H / 'public-api-output'))
    state['stage'] = 'uploading_and_submitting'
    save()
    job = client.submit(caption=None, image=None,
        mv_image_front=handle_file(str(H / 'front.png')),
        mv_image_back=handle_file(str(H / 'back.png')),
        mv_image_left=handle_file(str(H / 'left.png')),
        mv_image_right=handle_file(str(H / 'right.png')),
        steps=10, guidance_scale=5, seed=901010, octree_resolution=384,
        check_box_rembg=True, num_chunks=8000, randomize_seed=False,
        api_name=api_name)
    state['stage'] = 'request_started'
    save()
    previous = None
    while not job.done():
        status = job.status()
        compact = {'code': str(status.code), 'rank': status.rank,
                   'queue_size': status.queue_size, 'eta': status.eta,
                   'success': status.success}
        if compact != previous:
            state['remoteStatus'] = compact
            save()
            print('HEAD_JOB_STATUS', json.dumps(compact), flush=True)
            previous = compact
        time.sleep(15)
    result = job.result()
    (H / f'public-generation-result-{attempt}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    state['stage'] = 'completed'
    state['modelGenerated'] = True
    state['files'] = [item for item in result[:1 if shape_only else 2] if isinstance(item, str)]
    state['completedAt'] = datetime.now(timezone.utc).isoformat()
    save()
    print('HEAD_JOB_COMPLETED', json.dumps(state), flush=True)
except Exception as exc:
    state['stage'] = 'failed'
    state['errorType'] = type(exc).__name__
    state['error'] = str(exc)
    save()
    print('HEAD_JOB_FAILED', state['errorType'], state['error'], flush=True)
    raise
