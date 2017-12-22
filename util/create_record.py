import os
from glob import glob
import cv2

# Unused, replaced by built into app functionality

def main(cwd=None):
    if cwd is not None:
        cwd_p = os.getcwd()
        os.chdir(cwd)
    else:
        cwd_p = None
    print(os.getcwd())
    filenames = [f for f in glob("../screenshots/*.png")]
    images = [cv2.imread(f) for f in filenames]

    #H.264 MPEG-4
    fourcc = 0x00000021 #cv2.VideoWriter_fourcc(*"X264")
    writer = cv2.VideoWriter("record.mp4", fourcc, 30, (1024, 768), True)

    for image in images:
        writer.write(image)

    if cwd_p is not None:
        os.chdir(cwd_p)

if __name__ == "__main__":
    im = cv2.imread(glob("../screenshots/*.png")[0])
    print(im, type(im), im.shape)
    #main()