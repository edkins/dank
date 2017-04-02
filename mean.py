import PIL.Image
import sys
import os

filename='/home/giles/Pictures/ea memes/meanmeme/Screenshot from 2017-02-17 17-58-46.png'

startx=1056
wstartx=1500
endx=2773
starty=290
endy=2160

dirname='/home/giles/Pictures/ea memes/meanmeme/'

def whiterow(im,y):
	for x in range(wstartx,endx):
		if im.getpixel((x,y)) != (255,255,255):
			return False
	return True

def process(filename):
	if not filename.startswith('Screenshot') or not filename.endswith('.png'):
		print('Ignore ' + filename + '( wrong filename)') 
		return

	im = PIL.Image.open(dirname + filename, mode='r')
	if im.width != 3840 or im.height != 2160:
		print('Ignore ' + filename + ' (wrong size)')
		return

	starty1 = starty
	while not whiterow(im,starty1):
		starty1 += 1
	while whiterow(im,starty1):
		starty1 += 1

	endy1 = endy - 1
	while not whiterow(im,endy1):
		endy1 -= 1
	while whiterow(im,endy1):
		endy1 -= 1

	print(filename + ' height = ' + str(endy1-starty1) + ', starty=' + str(starty1) + ', endy = ' + str(endy1))

for filename in os.listdir(dirname):
	process(filename)

