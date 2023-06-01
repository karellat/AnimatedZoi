import json
import shutil
import cv2
import numpy as np

def main(config_path, image_path, output_path):
    with open(config_path) as config_file:
        config = json.load(config_file)
    image = cv2.imread(image_path)
    # calculate the coordinates of the character bounding box
    bbox = np.array(config[0]['bbox'])
    l, t, r, b = [round(x) for x in bbox]
    # crop the image
    cropped = image[t:b, l:r]
    # resize crop
    if np.max(cropped.shape) > 1000:
        scale = 1000 / np.max(cropped.shape)
        cropped = cv2.resize(cropped, (round(scale * cropped.shape[1]), round(scale * cropped.shape[0])))
    
    cv2.imwrite(output_path, cropped)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python script.py config_path image_path output_path")
        sys.exit(1)

    config_path = sys.argv[1]
    image_path = sys.argv[2]
    output_path = sys.argv[3]

    main(config_path, image_path, output_path)