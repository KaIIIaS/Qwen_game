import os, pygame
import settings
from utils import load_sprite
class MovingBackdrop:
 def __init__(self): self.key='asteroids'; self.x=0.0; self.speed=0.35; self.images={}
 def set(self,key): self.key=key
 def update(self): self.x=(self.x-self.speed)%settings.SCREEN_WIDTH
 def draw(self,s):
  name='bg_ruins' if self.key=='ruins' else 'bg_asteroids'
  im=self.images.get(name)
  if im is None:
   p=os.path.join(settings.ASSETS_DIR,name+'.jpg')
   if os.path.exists(p):
    raw=pygame.image.load(p).convert(); im=pygame.transform.smoothscale(raw,(settings.SCREEN_WIDTH,settings.SCREEN_HEIGHT)); self.images[name]=im
  if im:
   w=im.get_width(); x=int(self.x); s.blit(im,(x,0)); s.blit(im,(x-w,0)); s.blit(im,(x+w,0))
