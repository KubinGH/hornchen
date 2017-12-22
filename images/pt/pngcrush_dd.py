import glob, subprocess, os

for file in glob.glob("*.png"):
    subprocess.call(["pngcrush", "-ow", "-rem allb", "-reduce", file])