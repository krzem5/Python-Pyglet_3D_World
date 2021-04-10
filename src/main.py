from collections import deque
from pyglet.gl import *
from pyglet.window import key
import math
import random



class Perlin:
	def __call__(self,x,y): return (self.noise(x*self.f,y*self.f)+1)/2
	def __init__(self,seed=None):
		self.f = 15/512; self.m = 65535; p = list(range(self.m))
		if seed: random.seed(seed)
		random.shuffle(p); self.p = p+p

	def fade(self,t): return t*t*t*(t*(t*6-15)+10)
	def lerp(self,t,a,b): return a+t*(b-a)
	def grad(self,hash,x,y,z):
		h = hash&15; u = y if h&8 else x
		v = (x if h==12 or h==14 else z) if h&12 else y
		return (u if h&1 else -u)+(v if h&2 else -v)

	def noise(self,x,y,z=0):
		p,fade,lerp,grad = self.p,self.fade,self.lerp,self.grad
		xf,yf,zf = math.floor(x),math.floor(y),math.floor(z)
		X,Y,Z = xf%self.m,yf%self.m,zf%self.m
		x-=xf; y-=yf; z-=zf
		u,v,w = fade(x),fade(y),fade(z)
		A = p[X  ]+Y; AA = p[A]+Z; AB = p[A+1]+Z
		B = p[X+1]+Y; BA = p[B]+Z; BB = p[B+1]+Z
		return lerp(w,lerp(v,lerp(u,grad(p[AA],x,y,z),grad(p[BA],x-1,y,z)),lerp(u,grad(p[AB],x,y-1,z),grad(p[BB],x-1,y-1,z))),
					  lerp(v,lerp(u,grad(p[AA+1],x,y,z-1),grad(p[BA+1],x-1,y,z-1)),lerp(u,grad(p[AB+1],x,y-1,z-1),grad(p[BB+1],x-1,y-1,z-1))))
class Block:
	def __init__(self,name,pos,map_):
		if name in ['stone','dirt']:
			type_,tex='cube_all',[f'{name}.png']
		elif name in ['grass_block']:
			type_,tex='cube_topbottom',[f'{name}_top.png',f'{name}_side.png',f'{name}_bottom.png']
		else:
			raise RuntimeError
		if name=='grass_block':tex[2]='dirt.png'
		if type_=='cube_topbottom':self.w=self.s=self.e=self.n=self.get_tex(tex[1]);self.u=self.get_tex(tex[0]);self.d=self.get_tex(tex[2])
		elif type_=='cube_all':self.w=self.s=self.e=self.n=self.u=self.d=self.get_tex(tex[0])
		else:
			raise RuntimeError
		self.name=name
		self.batch=pyglet.graphics.Batch()
		tex_coords=('t2f',(0,0,1,0,1,1,0,1,))
		self.tex_coords=tex_coords
		self.pos=pos
		map_[tuple(pos)]=self
		self.update(map_)
	def draw(self):self.batch.draw()
	def get_tex(self,file):
		tex=pyglet.image.load('tex\\'+file).texture
		glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST)
		glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST)
		return pyglet.graphics.TextureGroup(tex)
	def update(self,map_,call=True):
		l,l2=[(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)],[False]*6
		for crds in l:
			x2,y2,z2=self.pos[0]+crds[0],self.pos[1]+crds[1],self.pos[2]+crds[2]
			if (x2,y2,z2) in list(map_.keys()):
				if map_[(x2,y2,z2)].name=='air':l2[l.index(crds)]=True
				elif call:
					map_[(x2,y2,z2)].update(map_,False)
			else:l2[l.index(crds)]=True
		x,y,z,X,Y,Z=self.pos[0],self.pos[1],self.pos[2],self.pos[0]+1,self.pos[1]+1,self.pos[2]+1
		self.batch=pyglet.graphics.Batch()
		if l2[0]:self.batch.add(4,GL_QUADS,self.w,('v3f',(x,y,z,x,y,Z,x,Y,Z,x,Y,z,)),self.tex_coords)
		if l2[1]:self.batch.add(4,GL_QUADS,self.s,('v3f',(X,y,Z,X,y,z,X,Y,z,X,Y,Z,)),self.tex_coords)
		if l2[2]:self.batch.add(4,GL_QUADS,self.d,('v3f',(x,y,z,X,y,z,X,y,Z,x,y,Z,)),self.tex_coords)
		if l2[3]:self.batch.add(4,GL_QUADS,self.u,('v3f',(x,Y,Z,X,Y,Z,X,Y,z,x,Y,z,)),self.tex_coords)
		if l2[4]:self.batch.add(4,GL_QUADS,self.e,('v3f',(X,y,z,x,y,z,x,Y,z,X,Y,z,)),self.tex_coords)
		if l2[5]:self.batch.add(4,GL_QUADS,self.n,('v3f',(x,y,Z,X,y,Z,X,Y,Z,x,Y,Z,)),self.tex_coords)
class Player:
	def __init__(self,pos=(0,0,0),rot=(0,0)):
		self.pos=list(pos)
		self.rot=list(rot)
		self.speed=1
	def mouse_motion(self,dx,dy):
		dx/=8;dy/=8;self.rot[0]+=dy;self.rot[1]-=dx
		if self.rot[0]>90:self.rot[0]=90
		elif self.rot[0]<-90:self.rot[0]=-90
	def update(self,dt,keys):
		s=dt*10
		rotY=-self.rot[1]/180*math.pi
		dx,dz=s*math.sin(rotY)*self.speed,s*math.cos(rotY)*self.speed
		if keys[key.W]:self.pos[0]+=dx;self.pos[2]-=dz
		if keys[key.S]:self.pos[0]-=dx;self.pos[2]+=dz
		if keys[key.A]:self.pos[0]-=dz;self.pos[2]-=dx
		if keys[key.D]:self.pos[0]+=dz;self.pos[2]+=dx
		if keys[key.SPACE]:self.pos[1]+=s
		if keys[key.LSHIFT]:self.pos[1]-=s
		if keys[key.UP]:self.speed+=1
		if keys[key.DOWN]:self.speed-=1
		if self.speed<1:self.speed=1
		if self.speed>5:self.speed=5
class Window(pyglet.window.Window):
	def push(self,pos,rot):glPushMatrix();glRotatef(-rot[0],1,0,0);glRotatef(-rot[1],0,1,0);glTranslatef(-pos[0],-pos[1],-pos[2],)
	def Projection(self):glMatrixMode(GL_PROJECTION);glLoadIdentity()
	def Model(self):glMatrixMode(GL_MODELVIEW);glLoadIdentity()
	def set2d(self):self.Projection();gluOrtho2D(0,self.width,0,self.height);self.Model()
	def set3d(self):self.Projection();gluPerspective(70,self.width/self.height,0.05,1000);self.Model()
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.map_={}
		self.set_minimum_size(800,600)
		self.keys=key.KeyStateHandler()
		self.push_handlers(self.keys)
		pyglet.clock.schedule(self.update)
		l=[]
		w,h=2,2
		for x in range(-w,w):
			for y in range(-h,h):l.append((x,y))
		l=sorted(l,key=lambda i:i[0]**2+i[1]**2)
		self.queue=deque(l)
		self.time=0
		self.player=Player((0,13,0),(-90,0))
		self.perlin=Perlin(1800)
		self.fps = pyglet.clock.ClockDisplay()
		#[Block('stone',[x,0,0],self.map_) for x in range(0,24,4)];[Block('dirt',[x,y,z],self.map_) for (x,y,z) in [(0,0,-1),(3,0,0),(8,-1,0),(12,1,0),(16,0,1),(21,0,0)]]
		[Block('stone',[x,0,z],self.map_) for (x,z) in [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),(16,0),(17,0),(18,0),(19,0),(20,0),(21,0),(22,0),(23,0),(24,0),(25,0),(26,0),(27,0),(0,1),(13,1),(14,1),(27,1),(0,2),(2,2),(3,2),(4,2),(5,2),(7,2),(8,2),(9,2),(10,2),(11,2),(13,2),(14,2),(16,2),(17,2),(18,2),(19,2),(20,2),(22,2),(23,2),(24,2),(25,2),(27,2),(0,3),(2,3),(3,3),(4,3),(5,3),(7,3),(8,3),(9,3),(10,3),(11,3),(13,3),(14,3),(16,3),(17,3),(18,3),(19,3),(20,3),(22,3),(23,3),(24,3),(25,3),(27,3),(0,4),(2,4),(3,4),(4,4),(5,4),(7,4),(8,4),(9,4),(10,4),(11,4),(13,4),(14,4),(16,4),(17,4),(18,4),(19,4),(20,4),(22,4),(23,4),(24,4),(25,4),(27,4),(0,5),(27,5),(0,6),(2,6),(3,6),(4,6),(5,6),(7,6),(8,6),(10,6),(11,6),(12,6),(13,6),(14,6),(15,6),(16,6),(17,6),(19,6),(20,6),(22,6),(23,6),(24,6),(25,6),(27,6),(0,7),(2,7),(3,7),(4,7),(5,7),(7,7),(8,7),(10,7),(11,7),(12,7),(13,7),(14,7),(15,7),(16,7),(17,7),(19,7),(20,7),(22,7),(23,7),(24,7),(25,7),(27,7),(0,8),(7,8),(8,8),(13,8),(14,8),(19,8),(20,8),(27,8),(0,9),(1,9),(2,9),(3,9),(4,9),(5,9),(7,9),(8,9),(9,9),(10,9),(11,9),(13,9),(14,9),(16,9),(17,9),(18,9),(19,9),(20,9),(22,9),(23,9),(24,9),(25,9),(26,9),(27,9),(5,10),(7,10),(8,10),(9,10),(10,10),(11,10),(13,10),(14,10),(16,10),(17,10),(18,10),(19,10),(20,10),(22,10),(5,11),(7,11),(8,11),(19,11),(20,11),(22,11),(5,12),(7,12),(8,12),(10,12),(11,12),(12,12),(15,12),(16,12),(17,12),(19,12),(20,12),(22,12),(0,13),(1,13),(2,13),(3,13),(4,13),(5,13),(7,13),(8,13),(10,13),(17,13),(19,13),(20,13),(22,13),(23,13),(24,13),(25,13),(26,13),(27,13),(10,14),(17,14),(0,15),(1,15),(2,15),(3,15),(4,15),(5,15),(7,15),(8,15),(10,15),(17,15),(19,15),(20,15),(22,15),(23,15),(24,15),(25,15),(26,15),(27,15),(5,16),(7,16),(8,16),(10,16),(11,16),(12,16),(13,16),(14,16),(15,16),(16,16),(17,16),(19,16),(20,16),(22,16),(5,17),(7,17),(8,17),(19,17),(20,17),(22,17),(5,18),(7,18),(8,18),(10,18),(11,18),(12,18),(13,18),(14,18),(15,18),(16,18),(17,18),(19,18),(20,18),(22,18),(0,19),(1,19),(2,19),(3,19),(4,19),(5,19),(7,19),(8,19),(10,19),(11,19),(12,19),(13,19),(14,19),(15,19),(16,19),(17,19),(19,19),(20,19),(22,19),(23,19),(24,19),(25,19),(26,19),(27,19),(0,20),(13,20),(14,20),(27,20),(0,21),(2,21),(3,21),(4,21),(5,21),(7,21),(8,21),(9,21),(10,21),(11,21),(13,21),(14,21),(16,21),(17,21),(18,21),(19,21),(20,21),(22,21),(23,21),(24,21),(25,21),(27,21),(0,22),(2,22),(3,22),(4,22),(5,22),(7,22),(8,22),(9,22),(10,22),(11,22),(13,22),(14,22),(16,22),(17,22),(18,22),(19,22),(20,22),(22,22),(23,22),(24,22),(25,22),(27,22),(0,23),(4,23),(5,23),(22,23),(23,23),(27,23),(0,24),(1,24),(2,24),(4,24),(5,24),(7,24),(8,24),(10,24),(11,24),(12,24),(13,24),(14,24),(15,24),(16,24),(17,24),(19,24),(20,24),(22,24),(23,24),(25,24),(26,24),(27,24),(0,25),(1,25),(2,25),(4,25),(5,25),(7,25),(8,25),(10,25),(11,25),(12,25),(13,25),(14,25),(15,25),(16,25),(17,25),(19,25),(20,25),(22,25),(23,25),(25,25),(26,25),(27,25),(0,26),(7,26),(8,26),(13,26),(14,26),(19,26),(20,26),(27,26),(0,27),(2,27),(3,27),(4,27),(5,27),(6,27),(7,27),(8,27),(9,27),(10,27),(11,27),(13,27),(14,27),(16,27),(17,27),(18,27),(19,27),(20,27),(21,27),(22,27),(23,27),(24,27),(25,27),(27,27),(0,28),(2,28),(3,28),(4,28),(5,28),(6,28),(7,28),(8,28),(9,28),(10,28),(11,28),(13,28),(14,28),(16,28),(17,28),(18,28),(19,28),(20,28),(21,28),(22,28),(23,28),(24,28),(25,28),(27,28),(0,29),(27,29),(0,30),(1,30),(2,30),(3,30),(4,30),(5,30),(6,30),(7,30),(8,30),(9,30),(10,30),(11,30),(12,30),(13,30),(14,30),(15,30),(16,30),(17,30),(18,30),(19,30),(20,30),(21,30),(22,30),(23,30),(24,30),(25,30),(26,30),(27,30)]]
		self.set_exclusive_mouse(1)
	def on_mouse_motion(self,x,y,dx,dy):self.player.mouse_motion(dx,dy)
	def update(self,dt):
		self.player.update(dt,self.keys)
		self.time-=dt
		if self.time<0:self.time=5
		if self.queue and self.time:self.gen(*self.queue.popleft())
	def on_draw(self):self.clear();self.set3d();self.push(self.player.pos,self.player.rot);[mdl.draw() for mdl in list(self.map_.values())];glPopMatrix();self.set2d();self.fps.draw()
	def gen(self,x,z):
		w,h=8,8;X,Z=x*(w-1),z*(h-1)
		for x in list(range(X,X+w)):
			for z in list(range(Z,Z+h)):
				h=int(self.perlin(x,z)*10)
				dirt=random.randint(2,3)
				for y in range(0,h+1):
					if 0<y<h-(dirt+1):Block('stone',[x,y,z],self.map_)
					if h-(dirt+2)<y<h:Block('dirt',[x,y,z],self.map_)
					if y==h:Block('grass_block',[x,y,z],self.map_)

if __name__ == '__main__':
	Window(width=854,height=480,caption='3D',resizable=False)
	glClearColor(0.5,0.7,1,1)
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)
	glDepthFunc(GL_LEQUAL); glAlphaFunc(GL_GEQUAL,1)
	glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
	pyglet.app.run()



