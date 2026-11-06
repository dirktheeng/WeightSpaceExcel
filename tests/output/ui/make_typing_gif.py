"""Observation only: types into a few cells one key per event batch through the full engine
(boot, main loop, kernel hooks), dumps the framebuffer after every batch and assembles the
frames into tests/output/ui/out/typing.gif for the README. Never opens weight files."""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ui_util as u  # noqa: E402
import blackbox as bb  # noqa: E402


def frame(h):
    px = h.mem[u.FB:u.FB + u.W * u.H].astype(np.int64).reshape(u.H, u.W)
    rgb = np.stack([(px >> 16) & 255, (px >> 8) & 255, px & 255], axis=-1).astype(np.uint8)
    return Image.fromarray(rgb[140:420, 0:640])


def main():
    h = u.harness([])
    out = h.run(0, np.zeros(65), max_steps=10**7)
    frames = [frame(h)]
    script = [bb.goto("B2")] + [bb.type_text(c) for c in "Apples"] + [bb.press(bb.VK_ENTER)] + \
        [bb.type_text(c) for c in "12.5"] + [bb.press(bb.VK_ENTER)] + \
        [bb.goto("C2")] + [bb.type_text(c) for c in "Fresh fruit"] + [bb.press(bb.VK_ENTER)] + \
        [bb.type_text(c) for c in "=1+2"] + [bb.press(bb.VK_ENTER)]
    for ev in script:
        h.events = ev
        out = h.run(4, np.concatenate([[0], out]), max_steps=10**7)
        frames.append(frame(h))
    path = os.path.join(u.OUT, "typing.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=180, loop=0)
    print(path, len(frames), "frames")


if __name__ == "__main__":
    main()
