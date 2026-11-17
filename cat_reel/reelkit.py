"""Shared plumbing for the Keef reels: scene timeline -> rendered, scored MP4."""
import math
import os
import subprocess
import sys

import cairo

from reel import W, H, FPS, seg, caption, end_card


def make_render(scenes, captions, end=None, punches=(), base_zoom=1.1):
    """scenes: [(start, end, fn(ctx, local_t))]; end: (t0, title_lines, subtitle)."""
    def render(ctx, t):
        ctx.save()
        z = 1.0 + sum(0.06 * math.exp(-(t - p) * 7) for p in punches if t >= p)
        ctx.translate(540, 1150)
        ctx.scale(z * base_zoom, z * base_zoom)
        ctx.translate(-540, -1150)
        for i, (a, b, fn) in enumerate(scenes):
            if a <= t < b or (i == len(scenes) - 1 and t >= b):
                fn(ctx, min(t, b) - a)
                break
        ctx.restore()
        caption(ctx, t, captions)
        if end and t >= end[0]:
            end_card(ctx, t - end[0], end[1], end[2])
        for a, _, _ in scenes[1:]:
            if a <= t < a + 0.2:
                ctx.rectangle(0, 0, W, H)
                ctx.set_source_rgba(1, 1, 1, 1 - seg(t, a, a + 0.2))
                ctx.fill()
        return ctx
    return render


def frame(render, t, dur):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    render(ctx, t)
    if t < 0.4:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0, 0, 0, 1 - seg(t, 0, 0.4))
        ctx.fill()
    if t > dur - 0.3:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(0, 0, 0, seg(t, dur - 0.3, dur))
        ctx.fill()
    surf.flush()
    return surf


def main(render, dur, soundtrack):
    """CLI: `video out.mp4` renders video + soundtrack and muxes them; `still out.png T`."""
    mode, out = sys.argv[1], sys.argv[2]
    if mode == 'still':
        frame(render, float(sys.argv[3]), dur).write_to_png(out)
        return
    silent, wav = out + '.video.mp4', out + '.audio.wav'
    proc = subprocess.Popen([
        'ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', silent
    ], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        proc.stdin.write(bytes(frame(render, i / FPS, dur).get_data()))
    proc.stdin.close()
    proc.wait()
    soundtrack(wav)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', silent, '-i', wav, '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    os.remove(silent)
    os.remove(wav)
