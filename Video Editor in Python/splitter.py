# Reference - https://stackoverflow.com/a/37323543
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# Split intervals in seconds
split_points = [(0,30),(48,80),(86,138),(170,232),(238,243)]

for point in split_points:
    ffmpeg_extract_subclip("../../vid.mp4", point[0], point[1], targetname="Vid-Final-"+str(point[1])+".mp4")

