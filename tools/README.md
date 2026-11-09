# Vape & Munchies content tools

Generates designed Instagram posts from staff photos. One post per product group; every photo is used once.

Setup (fresh machine):
    cd tools/fonts && npm install @fontsource/bungee @fontsource/barlow
    pip install onnxruntime opencv-python-headless pillow numpy
    curl -L -o /tmp/u2net.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx
    export VM_FONT_DIR=$PWD/fonts/node_modules/@fontsource VM_PHOTO_DIR=<folder with IMG_xxxx.JPG> VM_CUT_DIR=<cache folder>

Run: python3 posts.py <key>   (see POSTS in posts.py; reels: add `still 1 3 6` to preview frames)
Files: design.py (carousel + reel engine), cutout.py (background removal), music.py (original synthesized tracks), lib.py (drawing helpers).
Rules: no vape/nicotine/shisha products in frame, 19+ line on glass posts, no prices.
