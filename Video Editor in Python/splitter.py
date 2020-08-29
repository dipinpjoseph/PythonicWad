# Reference - https://stackoverflow.com/a/37323543
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# Split intervals in seconds
split_points = [(12,37),(57,186),(252,517),(608,627),(690,750)]

for point in split_points:
    ffmpeg_extract_subclip("2020-08-15 15-46-42.mkv", point[0], point[1], targetname="6Vid-Final-"+str(point[1])+".mp4")

