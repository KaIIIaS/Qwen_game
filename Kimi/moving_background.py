import os, pygame
import settings
class MovingBackground:
 def __init__(self): self.kind='asteroids'; self.offset=0.0; self.speed=0.45; self.cache={}
 def set(self,kind): self.kind=kind
 def update(self): self.offset=(self.offset-self.speed)%settings.SCREEN_WIDTH
 def draw(self,s):
  name='bg_ruins' if self.kind=='ruins' else 'bg_asteroids'; im=self.cache.get(name)
  if im is None:
   p=os.path.join(settings.ASSETS_DIR,name+'.jpg')
   if os.path.exists(p):
    im=pygame.image.load(p).convert(); im=pygame.transform.smoothscale(im,(settings.SCREEN_WIDTH,settings.SCREEN_HEIGHT)); self.cache[name]=im
  if im:
   x=int(self.offset); w=im.get_width(); s.blit(im,(x,0)); s.blit(im,(x-w,0)); s.blit(im,(x+w,0))
