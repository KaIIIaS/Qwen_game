import os, random, pygame
import settings
class Music:
    TRACKS=['ambient','battle','boss','nebula']
    def __init__(self, config):
        self.config=config; self.enabled=True; self.current=None; self.pending=True
    def start(self, kind='ambient'):
        if not self.enabled: return
        name=kind if kind in self.TRACKS else 'ambient'
        path=os.path.join(settings.ASSETS_DIR,'music',name+'.ogg')
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path); pygame.mixer.music.set_volume(float(self.config.get('music_volume',.4))*float(self.config.get('master_volume',.7))); pygame.mixer.music.play(-1); self.current=name
            except Exception: pass
    def stop(self):
        try: pygame.mixer.music.stop()
        except Exception: pass
        self.current=None
    def choose(self, kind):
        if kind!=self.current: self.start(kind)
