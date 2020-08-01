# https://stackoverflow.com/a/41991152
import os
from moviepy.editor import *

clips = []

for filename in os.listdir('.'):
    if filename.endswith(".mp4"):
        clips.append(VideoFileClip(filename))

video = concatenate_videoclips(clips, method='compose')
video.write_videofile('Vid-Merged.mp4')