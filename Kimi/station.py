"""Космическая станция: постоянные апгрейды и скины."""
import pygame
from settings import *
from utils import Button, draw_text, draw_panel, load_sprite, clamp

UPGRADES = {
 'hull': ('БРОНЯ', 'Больше жизней', 80, 5),
 'power': ('СИЛА ОРУЖИЯ', 'Урон основного оружия', 100, 5),
 'fire_rate': ('ТЕМП СТРЕЛЬБЫ', 'Быстрее перезарядка', 120, 5),
 'ship_speed': ('ДВИГАТЕЛИ', 'Скорость корабля', 90, 5),
 'drone_power': ('СИЛА ДРОНА', 'Урон дрона', 110, 5),
 'drone_rate': ('ЯДРО ДРОНА', 'Темп стрельбы дрона', 100, 5),
}
SKINS = [
 ('player', 'СТАНДАРТ', 0, (0,220,255)),
 ('player_neon', 'НЕОНОВЫЙ', 3, (255,80,220)),
 ('player_royal', 'КОРОЛЕВСКИЙ', 5, (255,210,60)),
 ('player_void', 'ПУСТОТНЫЙ', 8, (170,90,255)),
]

class Station:
 def __init__(self, game):
  self.game=game; self.tab='upgrades'; self.buttons=[]; self.build()
 def build(self):
  self.buttons=[]; W,H=SCREEN_WIDTH,SCREEN_HEIGHT; x=W//2-360; y=int(H*.25)
  if self.tab=='upgrades':
   for i,key in enumerate(UPGRADES):
    yy=y+i*72; self.buttons.append(Button(x+520,yy,58,54,'+',COLOR_GREEN,28,'buy:'+key))
   self.buttons.append(Button(W//2-330,int(H*.84),200,62,'СКИНЫ',(100,80,150),26,'skins'))
  else:
   for i,skin in enumerate(SKINS):
    self.buttons.append(Button(W//2-420+i*220,int(H*.38),190,110,skin[1],skin[3],22,'skin:'+skin[0],enabled=self.can_skin(skin[0])))
   self.buttons.append(Button(W//2-100,int(H*.84),200,62,'АПГРЕЙДЫ',(70,110,170),26,'upgrades'))
  self.buttons.append(Button(W//2+130,int(H*.84),200,62,'НАЗАД',(80,90,120),26,'back'))
 def can_skin(self,key):
  p=self.game.config.progress; return key in p.get('skins', ['player']) or p.get('faberge',0)>=next((s[2] for s in SKINS if s[0]==key),99)
 def click(self,pos):
  for b in self.buttons:
   if b.hit(pos):
    if b.value=='skins' or b.value=='upgrades': self.tab=b.value; self.build(); return None
    if b.value=='back': return 'back'
    if b.value.startswith('buy:'): return b.value
    if b.value.startswith('skin:'): return b.value
  return None
 def buy(self,key):
  p=self.game.config.progress; lvl=int(p.get('upgrades',{}).get(key,0)); _,_,base,mx=UPGRADES[key]
  cost=base*(lvl+1)
  if lvl<mx and p.get('coins',0)>=cost:
   p['coins']-=cost; p.setdefault('upgrades',{})[key]=lvl+1; self.game.audio.play('coin',.8); self.game.config.save(); return True
  return False
 def select_skin(self,key):
  p=self.game.config.progress; item=next(s for s in SKINS if s[0]==key)
  if key not in p.get('skins',['player']):
   if p.get('faberge',0)<item[2]: return False
   p['faberge']-=item[2]; p.setdefault('skins',['player']).append(key)
  p['skin']=key; self.game.config.save(); return True
 def draw(self,s):
  W,H=SCREEN_WIDTH,SCREEN_HEIGHT; p=self.game.config.progress
  draw_text(s,'КОСМИЧЕСКАЯ СТАНЦИЯ',58,W//2,int(H*.12),COLOR_WHITE,glow=True,glow_color=COLOR_CYAN)
  draw_text(s,'МОНЕТЫ: %d    ЯЙЦА ФАБЕРЖЕ: %d'%(p.get('coins',0),p.get('faberge',0)),26,W//2,int(H*.19),COLOR_GOLD)
  draw_text(s,'Прокачка сохраняется между забегами',20,W//2,int(H*.23),(170,180,200))
  if self.tab=='upgrades':
   x=W//2-360; y=int(H*.25)
   for i,(key,(name,desc,base,mx)) in enumerate(UPGRADES.items()):
    yy=y+i*72; lvl=int(p.get('upgrades',{}).get(key,0)); cost=base*(lvl+1)
    draw_panel(s,pygame.Rect(x,yy,590,58),(18,22,38),190,(55,75,110),10,2)
    draw_text(s,name,24,x+18,yy+17,COLOR_WHITE,center=False); draw_text(s,desc,16,x+18,yy+40,(145,155,180),center=False)
    draw_text(s,'%d / %d'%(lvl,mx),22,x+390,yy+29,COLOR_CYAN); draw_text(s,'%d монет'%cost,17,x+455,yy+29,COLOR_GOLD)
  else:
   draw_text(s,'СКИНЫ КОРАБЛЯ',30,W//2,int(H*.30),COLOR_CYAN)
   for i,(key,name,cost,col) in enumerate(SKINS):
    x=W//2-420+i*220; r=pygame.Rect(x,int(H*.38),190,110); unlocked=key in p.get('skins',['player']); selected=p.get('skin','player')==key
    draw_panel(s,r,(20,25,45),220,col if selected else (60,65,90),12,3)
    draw_text(s,name,20,r.centerx,r.top+28,col); draw_text(s,'ВЫБРАН' if selected else ('ОТКРЫТ' if unlocked else '%d яйца'%cost),18,r.centerx,r.top+78,COLOR_WHITE)
  for b in self.buttons: b.update(pygame.mouse.get_pos()); b.draw(s)
