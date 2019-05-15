import os
import sys
import random

with open('AppendList.txt','r') as append_file:
	append_list = [line.strip() for line in append_file.readlines()]

icon_name = ' '.join(sys.argv[1:])
dir_name = os.path.join(os.getcwd(), icon_name)

files = os.listdir(dir_name)
for file in files:
	os.rename(os.path.join(dir_name, file), os.path.join(dir_name, icon_name + " " + random.choice(append_list) + "." + file.split(".")[1]))
