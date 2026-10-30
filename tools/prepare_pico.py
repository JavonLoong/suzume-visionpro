"""Restore the pinned official PICO SDK and apply this project's compatibility patch."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SDK = ROOT / 'suzume-scene-prep/picounity/Packages/com.unity.xr.picoxr'
COMMIT = 'c93a59bab88d337fe0d54140499712897cedbe52'
PATCH = Path(__file__).with_name('pico-sdk.patch')


def git(*args, cwd=ROOT, check=True):
    return subprocess.run(['git', '-C', str(cwd), *args], check=check,
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


def main():
    git('submodule', 'update', '--init', '--recursive', '--', SDK.relative_to(ROOT).as_posix())
    actual = git('rev-parse', 'HEAD', cwd=SDK).stdout.strip()
    if actual != COMMIT:
        raise RuntimeError(f'Unexpected PICO SDK revision: {actual}; expected {COMMIT}')
    if git('apply', '--reverse', '--check', str(PATCH), cwd=SDK, check=False).returncode == 0:
        print('PICO SDK compatibility patch is already applied.')
    else:
        git('apply', '--check', str(PATCH), cwd=SDK)
        git('apply', str(PATCH), cwd=SDK)
        print('PICO SDK compatibility patch applied.')
    print('Ready: open suzume-scene-prep/picounity in Unity 2022.3.62f3.')
    print('The original PICO license remains in Packages/com.unity.xr.picoxr/LICENSE.md.')


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(getattr(exc, 'stderr', None) or str(exc), file=sys.stderr)
        sys.exit(1)
