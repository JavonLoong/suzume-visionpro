"""Read-only comparison of three fixed plaster samples, not a fidelity score."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

R = Path(__file__).parent
O = R / 'movie-material-v22'
baseline = json.loads((R / 'movie-windows-v21' / 'facade-color-gap-v21.json').read_text(encoding='utf-8'))
trials = []
for file in sorted(O.glob('facade-trial-*.png')):
    rgb = np.asarray(Image.open(file).convert('RGB'), dtype=float)
    rows = []
    for roi in baseline['regions']:
        x0, y0, x1, y1 = roi['renderBox']
        actual = np.median(rgb[y0:y1, x0:x1].reshape(-1, 3), axis=0)
        target = np.array(roi['referenceMedian'])
        rows.append({'region': roi['region'], 'renderMedian': actual.tolist(),
                     'referenceMedian': target.tolist(),
                     'rgbDistance': float(np.linalg.norm(actual-target))})
    trials.append({'name': file.stem, 'patches': rows,
                   'meanRgbDistance': float(np.mean([row['rgbDistance'] for row in rows]))})
result = {'scope': 'Three manually selected plaster patches only; not a whole-image score.',
          'phase': 'Initial light selection with v22 plaster and v21 window materials. The final scene also darkens glazing and window frames; final-color-comparison-v22.json records that result.',
          'trials': trials}
(O / 'color-trials-v22.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
for row in sorted(trials, key=lambda row: row['meanRgbDistance']):
    print(row['name'], round(row['meanRgbDistance'], 2), [p['renderMedian'] for p in row['patches']])
