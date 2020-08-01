# Reference - https://stackoverflow.com/questions/60940266/rotating-a-color-clip-in-moviepy

filename = "Vid_Final.mp4"

import moviepy.editor as mped
vid = mped.VideoFileClip(filename)
vid = vid.rotate(90)
vid.write_videofile('Vid_Rotate.mp4')


