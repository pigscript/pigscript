from urllib.request import urlopen
from PIL.ImageGrab import grab
from pymouse import PyMouse
from msvcrt import getch
from io import BytesIO
from PIL import Image
import random
import math
import time


class picture:

	def __init__(self, filename, theta, source):
		self.name = filename
		self.angle = theta
		self.source = source

	def load(self):
		color_list = [(0,0,0),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255),(255,255,255),(128,128,128)]
		tolerance = [128, 128, 128, 128, 128, 128, 128, 128, 400]
		rgb = [[0,0,0,1],[255,0,0,1],[0,255,0,1],[0,0,255,1],[255,255,0,1],[255,0,255,1],[0,255,255,1],[255,255,255,1],[128,128,128,1]]
		if self.source==1:
			im = Image.open(self.name)
		else:
			fd = urlopen(self.name)
			image_file = BytesIO(fd.read())
			im=Image.open(image_file)
		im = im.convert('RGBA')
		width, height = im.size
		rec = [[-1 for x in range(width)] for y in range(height)]
		pixdata = [[(255,255,255,255) for x in range(width)] for y in range(height)]
		cx = (width-1)/2
		cy = (height-1)/2
		ctheta = math.cos(self.angle)
		stheta = math.sin(self.angle)
		print('Loading picture, please wait')
		for x in range(width):
			for y in range(height):
				tx = cx + (x-cx)*ctheta - (y-cy)*stheta
				ty = cy + (x-cx)*stheta + (y-cy)*ctheta
				nx = round(tx)
				ny = round(ty)
				if nx<width and nx>=0 and ny<height and ny>=0:
					pixdata[y][x] = im.getpixel((nx,ny))
					r,g,b,a = pixdata[y][x]
					if a>150:
						for ind in range(8):
							r0,g0,b0 = color_list[ind]
							if abs(r-r0)+abs(g-g0)+abs(b-b0)<tolerance[ind]:
								rgb[ind][0]+=r
								rgb[ind][1]+=g
								rgb[ind][2]+=b
								rgb[ind][3]+=1
								rec[y][x]=ind
								break
							else:
								rgb[8][0]+=r
								rgb[8][1]+=g
								rgb[8][2]+=b
								rgb[8][3]+=1
								rec[y][x]=8
		for ind in range(9):
			rgb[ind][0] = round(rgb[ind][0]/rgb[ind][3])
			rgb[ind][1] = round(rgb[ind][1]/rgb[ind][3])
			rgb[ind][2] = round(rgb[ind][2]/rgb[ind][3])
	#	im1 = Image.new('RGBA',(width,height))
	#	print('The picture paint on the ball will look like this:')
	#	for x in range(width):
	#		for y in range(height):
	#			if rec[y][x]==-1:
	#				im1.putpixel((x,y),(255,255,255,0))
	#			else:
	#				r,g,b = rgb[rec[y][x]][:3]
	#				im1.putpixel((x,y),(r,g,b,255))
	#	im1.show()
		print('Estimated painting time is {} - {} minutes.'.format(width*height//20000, width*height//4000))
		print('Please switch to chrome browser and activate full screen mode.')
		print('Then switch back to this command window and press any key to start.')
		input()
		return pixdata, rgb

	def crop(self, pixdata, start_x, start_y, end_x, end_y):
		pixblock = [[(255,255,255,255) for x in range(end_x-start_x)] for y in range(end_y-start_y)]
		for y in range(start_y,end_y):
			for x in range(start_x,end_x):
				pixblock[y-start_y][x-start_x] = pixdata[y][x]
		return pixblock
		
	def parse(self, pixblock, ind, minlength=0):
		color_list = [(0,0,0),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255),(255,255,255),(128,128,128)]
		tolerance = [128, 128, 128, 128, 128, 128, 128, 128, 400]
		segments=[]
		height=len(pixblock)
		width=len(pixblock[0])
		red,green,blue=color_list[ind]
		tol = tolerance[ind]
		for j in range(height):
			flag = 0
			for i in range(width):
				r,g,b,a = pixblock[j][i]
				if abs(red-r)+abs(green-g)+abs(blue-b) <= tol and a>150:
					pixblock[j][i] = (255,255,255,0)
					if flag==0:
						flag = 1
						xl = i
				else:
					if flag==1:
						flag=0
						xr = i-1
						if xr-xl>=minlength:
							segments.append((j,xl,xr))
			if flag==1:
				xr=i
				if xr-xl>=minlength:
					segments.append((j,xl,xr))
		return segments, pixblock

	def filtration(self, pixblock, red, green, blue, tolerance, minlength=0):
		height = len(pixblock)
		width = len(pixblock[0])
		segments = []
		for j in range(height):
			flag = 0
			for i in range(width):
				r,g,b = pixblock[j][i]
				if abs(red-r)+abs(green-g)+abs(blue-b) < tolerance:
					pixblock[j][i] = (255,255,255)
					if flag==0:
						flag = 1
						xl = i
				else:
					if flag==1:
						flag=0
						xr = i
						if xr-xl>=minlength:
							segments.append((j,xl,xr,r,g,b))
			if flag==1:
				xr=i
				if xr-xl>=minlength:
					segments.append((j,xl,xr,r,g,b))
		return segments, pixblock


class paint:	
	
	def __init__(self, mouse, flag=0):
		self.mouse = mouse
		self.scr_width, self.scr_height = mouse.screen_size()
		self.center_x = 170 + self.scr_width//2
		self.center_y = self.scr_height//2
		if self.scr_width==12800 or self.scr_width==13660:
			self.wheel_x = 502 + self.scr_width//2
			self.wheel_y = 212 + self.scr_height//2
			self.radius = 31
		else:
			self.wheel_x, self.wheel_y, self.radius = 0,0,0
	
	def shift(self, dir, t):
		if dir == 'up':
			self.mouse.move(self.center_x, self.center_y - 318)
		elif dir == 'down':
			self.mouse.move(self.center_x, self.center_y + 318)
		elif dir == 'left':
			self.mouse.move(self.center_x - 318, self.center_y)
		elif dir == 'right':
			self.mouse.move(self.center_x + 318, self.center_y)
		time.sleep(t)
		self.mouse.move(self.center_x, self.center_y)

	def drift(self, dir, t, x0, y0, vec1, vec2):
		self.shift(dir,t)
		time.sleep(3)
		self.mouse.move(1,1)
		im = grab()
		data = [sum(im.getpixel((x0+k*vec1, y0+k*vec2))[:3]) for k in range(409)]
		for k in range(401):
			if data[k] < 100:
				if max(data[k+1:k+3])>650 and min(data[k+2:k+5])<100 and max(data[k+3:k+6])>650 and min(data[k+4:k+7])<100:
					print(data[k-1:k+8])
					return k
		print('Bad')
		print(data)
		return -1
		
	def setmouse(self):
		print('I need more information about your screen size')
		print('Please use asdw keys to put the mouse near the center of the big ball, then press enter.')
		x=self.center_x
		y=self.center_y
		while True:
			c=getch().decode()
			if c=='a':
				x-=1
			elif c=='d':
				x+=1
			elif c=='w':
				y-=1
			elif c=='s':
				y+=1
			elif c=='\r' or c=='\n':
				break
			self.mouse.move(x,y)
		self.center_x = x
		self.center_y = y

		x = 502 + self.scr_width//2
		y = 212 + self.scr_height//2
		print('Please use asdw keys to put the mouse near the center of the color wheel, then press enter.')
		while True:
			c=getch().decode()
			if c=='a':
				x-=1
			elif c=='d':
				x+=1
			elif c=='w':
				y-=1
			elif c=='s':
				y+=1
			elif c=='\r' or c=='\n':
				break
			self.mouse.move(x,y)
		self.mouse.click(x,y-15)
		time.sleep(0.1)
		im=grab()
		maxr = 0
		maxj = 0
		cx = 0
		lv=0
		for j in range(-8,9):
			data=[sum(im.getpixel((x-50+k,y+j))) for k in range(100)]
			left, right = -1,0
			for k in range(100):
				if data[k]<60:
					if left<0:
						left=k
					elif k-left>10:
						right=k
						break
			radius = right-left
			if radius>maxr:
				maxr=radius
				maxj = j
				cx=(left+right+1)//2
			elif radius==maxr:
				lv+=1
				
		x += cx-50
		y += maxj+lv//2
		self.mouse.click(x+15,y)
		time.sleep(0.1)
		im=grab()
		data=[sum(im.getpixel((x,y+j-40))) for j in range(81)]
		top,bottom=-1,-1
		for k in range(40):
			if data[40-k]<300:
				if top<0:
					top=k
			if data[40+k]<200:
				if bottom<0:
					bottom=k
		y = y+(bottom-top)//2
		self.mouse.click(x,y)
		radius = (top+bottom)//2
		return x,y,radius

	def setcolor(self, r, g, b, rainbow=0):
		if self.wheel_x == 0:
			self.wheel_x, self.wheel_y, self.radius = self.setmouse()
			
		wheel_x = self.wheel_x
		wheel_y = self.wheel_y
		wheel_r = self.radius
		bar_x = self.wheel_x+wheel_r+15
		if rainbow == 1:
			xt = wheel_x + round(wheel_r*math.cos(2*math.pi*r))
			yt = wheel_y - round(wheel_r*math.sin(2*math.pi*r))
			self.mouse.click(xt,yt)
			self.mouse.click(bar_x,wheel_y)
			return
		r,g,b = r/255, g/255, b/255
		maxc = max(r, g, b)
		minc = min(r, g, b)
		z = (maxc+minc)/2
		if minc == maxc:
			x,y = 0,0
		else:
			sc = (maxc-minc)/math.sqrt(r*r+g*g+b*b-r*g-g*b-b*r)
			x = (r - g/2 - b/2) * sc
			y = (math.sqrt(3)/2) * (g-b) * sc
		if x>0:
			xt = wheel_x + math.floor(wheel_r*x)
		else:
			xt = wheel_x + math.ceil(wheel_r*x)
		if y>0:
			yt = wheel_y - math.floor(wheel_r*y)
		else:
			yt = wheel_y - math.ceil(wheel_r*y)
		zt = wheel_y + wheel_r - round(2*wheel_r*z)
		self.mouse.click(xt,yt)
		self.mouse.click(bar_x,zt)

	def drawline(self, startx, starty, endx, endy):
		self.mouse.press(startx, starty)
		self.mouse.drag(endx, endy)
		time.sleep(0.1)
		self.mouse.release(endx, endy)
		if abs(endx-startx) > 40 or abs(endy-starty)>40:
			self.mouse.click(endx,endy)
			time.sleep(0.1)

	def barcode(self, startx, starty, dirx, diry, norx, nory, clean=False, color=(0,0,0)):
		barnum = 10
		barlen = 15
		if clean == False:
			im=grab()
			r,g,b=im.getpixel((startx,starty))
			barnum = 9
			barlen = 12
	
		for i in range(barnum):
			if clean==True:
				r,g,b=color
				self.setcolor(r,g,b)
			else:
				col = 255*((i%4)//2)
				self.setcolor(col,col,col)

			self.drawline(startx+norx*i, starty+nory*i, startx+norx*i+dirx*barlen, starty+nory*i+diry*barlen)
			time.sleep(0.1)
		return r,g,b
		
	def drawblock(self, segments, startx, starty, red, green, blue, scale=2):
		if len(segments)>0:
			self.setcolor(red,green,blue)
		for seg in segments:
			y,xl,xr = seg
			self.drawline(startx+scale*xl, starty+scale*y, startx+scale*xr, starty+scale*y)

	def drawblock2(self, segments, startx, starty, scale=1, color = 'auto', rgb=(0,0,0), rbht=0, rbst = 0):
		if len(segments)==0:
			return
		height = segments[-1][0] - segments[0][0]
		top = segments[0][0]
		if color == 'transparent':
			return
		elif color == 'black':
			self.setcolor(0,0,0)
		elif color == 'white':
			self.setcolor(255,255,255)
		elif color == 'gray':
			self.setcolor(128,128,128)
		elif color == 'red':
			self.setcolor(255,0,0)
		elif color == 'green':
			self.setcolor(0,255,0)
		elif color == 'blue':
			self.setcolor(0,0,255)
		elif color == 'yellow':
			self.setcolor(255,255,0)
		elif color == 'magenta':
			self.setcolor(255,0,255)
		elif color == 'cyan':
			self.setcolor(0,255,255)
		elif color == 'random':
			r = random.randint(0,255)
			g = random.randint(0,255)
			b = random.randint(0,255)
			self.setcolor(r,g,b)
			print("  Random color:",r,g,b)
		elif color == 'rgb':
			r,g,b=rgb
			self.setcolor(r,g,b)
		for seg in segments:
			y,xl,xr,cr,cg,cb = seg
			if color == 'auto':
				self.setcolor(cr,cg,cb)
			elif color == 'rainbow':
				if rbht==0:
					colp = (y-top)/height
				else:
					colp = (y+rbst)/rbht
				self.setcolor(colp,0,0,rainbow=1)
			elif color == 'noise':
				self.setcolor(random.randint(0,255),random.randint(0,255),random.randint(0,255))
			self.drawline(startx+scale*xl, starty+scale*y, startx+scale*xr, starty+scale*y)

	def autodraw(self, filename, source, scale=2, theta=0):
		pic = picture(filename, theta, source)
		pixdata,rgb = pic.load()
		height = len(pixdata)
		width = len(pixdata[0])
		xr, yr = 0, 0
		ulx, uly = 0, 0
		self.setcolor(255,255,255)
		time.sleep(1)
		safec = 5
		while True:
			ulx=0
			while True:
				if ulx>0:
					self.barcode(self.center_x+xr+safec-200, self.center_y-5,0,1,1,0,clean=True, color=(r1,g1,b1))
				if ulx+(400-xr)//scale < width:
					self.mouse.move(self.center_x, self.center_y)
					r1,g1,b1 = self.barcode(self.center_x+200+safec,self.center_y-5,0,1,1,0)
				if ulx==0:
					if uly>0:
						self.barcode(self.center_x+xr-safec-201, self.center_y+yr+safec-200,1,0,0,1,clean=True, color=(r2,g2,b2))
						self.barcode(self.center_x+xr-safec-201, self.center_y+yr+safec-200,0,-1,-1,0,clean=True, color=(r2,g2,b2))
					if uly+(400-yr)//scale < height:
						r2,g2,b2 = self.barcode(self.center_x+xr-201-safec, self.center_y+safec+200,1,0,0,1)
						r3,g3,b3 = self.barcode(self.center_x+xr-201-safec, self.center_y+safec+200,0,-1,-1,0)
				sx = max(ulx-1,0)
				sy = max(uly-1,0)
				ex = min(1+ulx+(400-xr)//scale, width-1)
				ey = min(1+uly+(400-yr)//scale, height-1)
				pixblock = pic.crop(pixdata,sx,sy,ex,ey)

				for ind in range(9):
					seg,pixblock = pic.parse(pixblock, ind, minlength=1)
					red,green,blue = rgb[ind][:3]
					self.drawblock(seg, self.center_x+xr-200, self.center_y+yr-200, red, green, blue, scale)
				time.sleep(0.5)

				ulx = ulx + (400-xr)//scale
				if ulx>=width:
					break

				xr = self.drift('right', 1, self.center_x-200, self.center_y, 1, 0)
				if xr<0:
					break
				while xr >= 100:
					xr = self.drift('right', xr/400, self.center_x-200, self.center_y, 1, 0)
					while xr<=0:
						xr = self.drift('left', 0.5, self.center_x-200, self.center_y, 1, 0)
				xr-=safec

			uly = uly + (400-yr)//scale
			if uly>=height:
				break
			xr = self.drift('left', 2, self.center_x+199, self.center_y+200, -1, 0)
			while xr==-1:
				xr = self.drift('left', 1, self.center_x+199, self.center_y+200, -1,0)
			while xr<=300:
				xr = self.drift('right', (400-xr)/400, self.center_x+199, self.center_y+200, -1,0)
				while xr<0:
					xr = self.drift('left', 0.5, self.center_x+199, self.center_y+200, -1,0)
			xr = 400-xr
			xr+=safec

			yr = self.drift('down', 1, self.center_x+xr-200, self.center_y-200, 0, 1)
			while yr >= 100:
				yr = self.drift('down', yr/400, self.center_x+xr-200, self.center_y-200, 0, 1)
				while yr<=0:
					yr = self.drift('up', 0.5, self.center_x+xr-200, self.center_y-200, 0, 1)
			yr-=safec

def main():
	m=PyMouse()
	pen = paint(m)
	print('Welcome to PigScript 1.0, please email pigscript@gmail.com for your feedback.')
	while True:
		s = input('Enter 1 for local pictures, enter 2 for website pictures: ')
		if s=='1' or s=='2':
			source = int(s)
			break
	if source==1:
		filename = input('Picture name: ')
	else:
		filename = input('URL of the picture: ')
	sc = input('Enter your pen size (1-30, default is 2): ')
	try:
		sc = int(sc)
	except:
		sc = 2
	if sc<1 or sc>30:
		sc=2
	pen.autodraw(filename, source, sc)

#main
while True:
	main()
	
	
	
	
	
	