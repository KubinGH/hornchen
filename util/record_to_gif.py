from moviepy.editor import VideoFileClip

clip = (VideoFileClip("../record.mp4")
        .resize(0.2)
        .speedx(4))
clip.preview()
clip.write_gif("record.gif")