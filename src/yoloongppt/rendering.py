"""SYS-014: actual isolated LibreOffice/PDF/PNG rendering, hashed by the run store."""
import os
import signal
import subprocess
from pathlib import Path

from .artifacts import entity, sha256
from .errors import TaskError


def process(args, timeout=120):
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.communicate()
        raise TaskError('RENDER_TIMEOUT', '渲染超时，已停止该进程组；未使用缓存或空图替代。', 'Renderer', ['SYS-014'], status=504) from None
    if child.returncode != 0:
        raise TaskError('RENDER_FAILED', '渲染命令失败；没有产生通过结论。', 'Renderer', ['SYS-014'], [{'exit_code': child.returncode}], status=500)
    return stdout.decode('utf-8', errors='strict'), stderr.decode('utf-8', errors='strict')


def render(pptx, deck, root):
    folder = Path(root) / 'render'; folder.mkdir(exist_ok=False)
    profile = folder / 'libreoffice-profile'
    lo, _ = process(['libreoffice', '--version'])
    _, poppler = process(['pdftoppm', '-v'])
    out, err = process(['libreoffice', '-env:UserInstallation='+profile.as_uri(), '--headless', '--convert-to',
                        'pdf:impress_pdf_Export', '--outdir', str(folder), str(pptx)])
    pdf = folder / (Path(pptx).stem + '.pdf')
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise TaskError('RENDER_OUTPUT_MISSING', 'LibreOffice未产生PDF。', 'Renderer', ['SYS-014'], status=500)
    process(['pdftoppm', '-png', '-r', '120', str(pdf), str(folder/'slide')])
    process(['pdftotext', '-layout', str(pdf), str(folder/'deck.txt')])
    process(['pdftotext', '-bbox', str(pdf), str(folder/'deck-bbox.xhtml')])
    images = sorted(folder.glob('slide-*.png'))
    if len(images) != len(deck['slides']):
        raise TaskError('RENDER_PAGE_COUNT_MISMATCH', '实际渲染页数与DeckSpec不同。', 'Renderer', ['SYS-014'], status=500)
    artifacts = [{'artifact_id': entity('artifact'), 'slide_id': None, 'type': 'pdf', 'path': str(pdf.relative_to(root)),
                  'hash': sha256(pdf), 'renderer': 'LibreOffice', 'version': lo.strip(), 'dpi': None}]
    for slide, image in zip(deck['slides'], images):
        artifacts.append({'artifact_id': entity('artifact'), 'slide_id': slide['slide_id'], 'type': 'png',
                          'path': str(image.relative_to(root)), 'hash': sha256(image), 'renderer': 'LibreOffice + pdftoppm',
                          'version': lo.strip()+'; '+poppler.splitlines()[0], 'dpi': 120})
    # Per-run profile stays inside F:; keep render artifacts, remove only this
    # isolated ephemeral profile after the process completed.
    import shutil
    shutil.rmtree(profile, ignore_errors=True)
    return {'artifacts': artifacts, 'renderer_version': lo.strip(), 'poppler_version': poppler.splitlines()[0],
            'stdout': out.strip(), 'stderr': err.strip(), 'powerpoint_compatibility': 'not_tested',
            'render_text_path': 'render/deck.txt','render_bbox_path':'render/deck-bbox.xhtml'}
