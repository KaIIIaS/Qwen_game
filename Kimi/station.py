import math, pygame
from settings import *
from utils import Button, draw_text, draw_panel, load_sprite, draw_progress_bar
UPGRADES={'hull':('БРОНЯ','+ максимум жизней',80,5),'power':('СИЛА','+ урон оружия',100,5),'fire_rate':('ТЕМП СТРЕЛЬБЫ','быстрее атака',120,5),'ship_speed':('ДВИГАТЕЛИ','быстрее движение',90,5),'drone_power':('СИЛА ДРОНА','+ урон дрона',110,5),'drone_rate':('ЯДРО ДРОНА','быстрее дрон',100,5)}
SKINS=[('player','СТАНДАРТ',0,(0,220,255)),('player_neon','НЕОН',3,(255,70,220)),('player_royal','КОРОЛЕВСКИЙ',5,(255,210,60)),('player_void','ПУСТОТА',8,(170,90,255)),('player_titan','ТИТАН',12,(255,100,60))]
class Station:
 def __init__(self,game): self.game=game; self.tab='upgrades'; self.buttons=[]; self.preview_t=0; self.build()
 def build(self):
  self.buttons=[]; W,H=SCREEN_WIDTH,SCREEN_HEIGHT
  self.buttons += [Button(W//2-330,int(H*.83),220,64,'СКИНЫ',(90,70,150),26,'skins'),Button(W//2+110,int(H*.83),220,64,'НАЗАД',(80,90,120),26,'back')]
  if self.tab=='upgrades':
   for i,k in enumerate(UPGRADES): self.buttons.append(Button(W//2+260,int(H*.23)+i*70,58,54,'+',COLOR_GREEN,30,'buy:'+k))
  else:
   for i,(k,n,c,col) in enumerate(SKINS): self.buttons.append(Button(W//2-460+i*230,int(H*.42),205,110,n,col,22,'skin:'+k,enabled=self.unlocked(k)))
   self.buttons[0]=Button(W//2-330,int(H*.83),220,64,'АПГРЕЙДЫ',(70,110,170),24,'upgrades')
 def unlocked(self,k): return k in self.game.config.progress.get('skins',['player']) or self.game.config.progress.get('faberge',0)>=next(x[2] for x in SKINS if x[0]==k)
 def click(self,pos):
  for b in self.buttons:
   if b.hit(pos): return b.value
  return None
 def buy(self,k):
  p=self.game.config.progress; lvl=int(p.get('upgrades',{}).get(k,0)); _,_,base,mx=UPGRADES[k]; cost=base*(lvl+1)
  if lvl<mx and p.get('coins',0)>=cost: p['coins']-=cost; p.setdefault('upgrades',{})[k]=lvl+1; self.game.config.save(); return True
  return False
 def skin(self,k):
  p=self.game.config.progress; item=next(x for x in SKINS if x[0]==k)
  if k not in p.get('skins',['player']):
   if p.get('faberge',0)<item[2]: return False
   p['faberge']-=item[2]; p.setdefault('skins',['player']).append(k)
  p['skin']=k; self.game.config.save(); return True
 def draw(self,s):
  self.preview_t+=.08; W,H=SCREEN_WIDTH,SCREEN_HEIGHT; p=self.game.config.progress
  draw_text(s,'КОСМИЧЕСКАЯ СТАНЦИЯ',56,W//2,int(H*.09),COLOR_WHITE,glow=True,glow_color=COLOR_CYAN)
  draw_text(s,'МОНЕТЫ: %d    ЯЙЦА ФАБЕРЖЕ: %d'%(p.get('coins',0),p.get('faberge',0)),25,W//2,int(H*.16),COLOR_GOLD)
  # живой preview корабля, оружия и дрона
  cx,cy=W//2-260,int(H*.48); pygame.draw.circle(s,(12,22,40),(cx,cy),145,2)
  ship=load_sprite(p.get('skin','player'),(96,120));
  if ship: s.blit(ship,ship.get_rect(center=(cx,cy+math.sin(self.preview_t)*4)))
  lvl=int(p.get('upgrades',{}).get('power',0))+1; guns=min(12,lvl)
  for i in range(guns):
   ox=(i-(guns-1)/2)*12; pygame.draw.line(s,COLOR_ORANGE,(cx+ox,cy-58),(cx+ox,cy-110),4)
  draw_text(s,'ОРУДИЙ: %d   УРОВЕНЬ: %d'%(guns,lvl),20,cx,cy+165,COLOR_ORANGE)
  if self.tab=='upgrades':
   x=W//2+40; y=int(H*.23)
   for i,(k,(n,d,b,mx)) in enumerate(UPGRADES.items()):
    yy=y+i*70; lv=int(p.get('upgrades',{}).get(k,0)); draw_panel(s,pygame.Rect(x,yy,500,56),(18,22,38),210,(60,80,120),10,2); draw_text(s,n,22,x+14,yy+17,COLOR_WHITE,center=False); draw_text(s,'%d/%d'%(lv,mx),20,x+330,yy+17,COLOR_CYAN); draw_text(s,'%d монет'%(b*(lv+1)),16,x+14,yy+41,COLOR_GOLD,center=False)
  else:
   draw_text(s,'СКИНЫ КОРАБЛЯ',28,W//2,int(H*.29),COLOR_CYAN)
   for i,(k,n,c,col) in enumerate(SKINS):
    r=pygame.Rect(W//2-460+i*230,int(H*.42),205,110); sel=p.get('skin','player')==k; draw_panel(s,r,(20,25,45),220,col if sel else (70,75,95),12,3); draw_text(s,n,20,r.centerx,r.top+28,col); draw_text(s,'ВЫБРАН' if sel else ('ОТКРЫТ' if self.unlocked(k) else '%d яйца'%c),17,r.centerx,r.top+78,COLOR_WHITE)
  for b in self.buttons: b.update(pygame.mouse.get_pos()); b.draw(s)
