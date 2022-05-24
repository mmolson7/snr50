
import os

#To rename the IEEE audio files for sorting
for filename in os.listdir('.\\audio\\IEEE'):
    filename = myPath + filename
    sep = ' '
    clipped = filename.split(sep,1)[0]
    just_nums = clipped[2:]
    os.rename(filename, just_nums)


for filename in os.listdir('.\\audio\\IEEE'):
    os.rename(r'.\\audio\\IEEE\\'+filename,r'.\\audio\\IEEE\\'+filename[2:]+'.wav')


"""
Works for slicing and ordering file names, 
but doesn't actually change them.
sep = ' ' 
clipped = [x.split(sep,1)[0] for x in fileList]
just_nums = [x[2:] for x in clipped]
fileList = sorted(just_nums, key = int)
#print(fileList)
"""