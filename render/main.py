from typing import Union
import uvicorn
from fastapi import FastAPI
import tempfile
from pathlib import Path
import logging
import yaml
import os
from glob import glob
import random
from io import BytesIO
from fastapi.responses import StreamingResponse
from typing import Optional
from typing_extensions import Annotated
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from skimage import measure
import animated_drawings.render
from scipy import ndimage

import numpy as np
import cv2

MOTION_DIR = './config/motion' 
RETARGET_CFG = './config/retarget/fair1_ppf.yaml' 
MASK_FILE = "mask.png"
TEXTURE_FILE = "texture.png"
CHARACTER_CONFIG = "char_cfg.yaml"
logger = logging.getLogger(__name__) 
app = FastAPI()


def segment(img: np.ndarray):
    """ threshold """
    img = np.min(img, axis=2)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 115, 8)
    img = cv2.bitwise_not(img)

    """ morphops """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=2)
    img = cv2.morphologyEx(img, cv2.MORPH_DILATE, kernel, iterations=2)

    """ floodfill """
    mask = np.zeros([img.shape[0]+2, img.shape[1]+2], np.uint8)
    mask[1:-1, 1:-1] = img.copy()

    # im_floodfill is results of floodfill. Starts off all white
    im_floodfill = np.full(img.shape, 255, np.uint8)

    # choose 10 points along each image side. use as seed for floodfill.
    h, w = img.shape[:2]
    for x in range(0, w-1, 10):
        cv2.floodFill(im_floodfill, mask, (x, 0), 0)
        cv2.floodFill(im_floodfill, mask, (x, h-1), 0)
    for y in range(0, h-1, 10):
        cv2.floodFill(im_floodfill, mask, (0, y), 0)
        cv2.floodFill(im_floodfill, mask, (w-1, y), 0)

    # make sure edges aren't character. necessary for contour finding
    im_floodfill[0, :] = 0
    im_floodfill[-1, :] = 0
    im_floodfill[:, 0] = 0
    im_floodfill[:, -1] = 0

    """ retain largest contour """
    mask2 = cv2.bitwise_not(im_floodfill)
    mask = None
    biggest = 0

    contours = measure.find_contours(mask2, 0.0)
    for c in contours:
        x = np.zeros(mask2.T.shape, np.uint8)
        cv2.fillPoly(x, [np.int32(c)], 1)
        size = len(np.where(x == 1)[0])
        if size > biggest:
            mask = x
            biggest = size

    if mask is None:
        msg = 'Found no contours within image'
        logging.critical(msg)
        assert False, msg

    mask = ndimage.binary_fill_holes(mask).astype(int)
    mask = 255 * mask.astype(np.uint8)

    return mask.T

def select_random_motion_cfg(fixed_id: Optional[int]=None):
    file_paths = []
    for root, dirs, files in os.walk(MOTION_DIR):
        for file in files:
            file_paths.append(os.path.join(root, file))

    if fixed_id:
        assert fixed_id < len(file_paths) and fixed_id > 0
        return file_paths[fixed_id]
    else:
        return random.choice(file_paths)

def choose_retarget_cfg(motion_cfg):
    file_name = os.path.basename(motion_cfg) 
    if file_name == "jesse_dance.yaml": 
        return './config/retarget/mixamo_fff.yaml'
    elif file_name == "jumping_jacks.yaml":
        return './config/retarget/cmu1_pfp.yaml'
    else: 
        return './config/retarget/fair1_ppf.yaml'


@app.get("/ping")
def read_ping():
    return {"Response": "Healthy"}

@app.post("/render")
async def render(image: UploadFile=File(...),
                 char_cfg: UploadFile=File(...),
                 motion_id: int=Form(...)):
    try: 
        temp_dir = tempfile.TemporaryDirectory()
        print(f"Created tmp dir: {temp_dir.name}")
        chr_cfg_path = os.path.join(temp_dir.name, CHARACTER_CONFIG) 
        texture_file = os.path.join(temp_dir.name, TEXTURE_FILE ) 
        mask_file = os.path.join(temp_dir.name, MASK_FILE)

        # Read pose keypoints
        with open(chr_cfg_path, 'wb') as f: 
            f.write(await char_cfg.read())
        # Read texture image
        with open(texture_file, 'wb') as f:
            f.write(await image.read())
        # Create mask
        img = cv2.imread(texture_file)
        mask = segment(img)
        cv2.imwrite(mask_file, mask)
        random_motion_cfg = select_random_motion_cfg(motion_id)
        animated_drawing_dict = {
        'character_cfg': chr_cfg_path,
        'motion_cfg': random_motion_cfg,
        'retarget_cfg': choose_retarget_cfg(random_motion_cfg)}
        print(animated_drawing_dict)

        # create mvc config
        output_gif = str(Path(temp_dir.name, 'video.gif').resolve())
        mvc_cfg = {
            'scene': {'ANIMATED_CHARACTERS': [animated_drawing_dict]},  
            'controller': {
                'MODE': 'video_render', 
                'OUTPUT_VIDEO_PATH': output_gif}  
        }

        # write the new mvc config file out
        output_mvc_cfn_fn = str(Path(temp_dir.name, 'mvc_cfg.yaml'))
        with open(output_mvc_cfn_fn, 'w') as f:
            yaml.dump(dict(mvc_cfg), f)

        # render the video
        animated_drawings.render.start(output_mvc_cfn_fn)
        with open(output_gif, 'rb') as f:
            img_raw = f.read()
        byte_io = BytesIO(img_raw)
        return StreamingResponse(byte_io, media_type='image/gif')

    finally: 
        print(f"Deleting tmp dir: {temp_dir.name}")
        temp_dir.cleanup()

    return  HTTPException(status_code=418, detail="Processing failed!")