import pygame
import math
import random
import pathlib
import pickle
from vector import Vector2

  
# ======================================================================
# constants to help code readability
# ======================================================================

GAME_MODE_LIVE            = 0
GAME_MODE_REPLAY          = 1
GAME_STATE_INTRO          = 0
GAME_STATE_IN_PROGRESS    = 1
GAME_STATE_WAVE_OVER      = 2
GAME_STATE_LAST_BASE_LOST = 3
GAME_STATE_OVER           = 4
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
ORIGINX = SCREEN_WIDTH // 2
ORIGINY = SCREEN_HEIGHT // 2
COLOUR_BLACK      = [0,0,0]
COLOUR_WHITE      = [255,255,255]
COLOUR_STARS      = [100,50,255]
COLOUR_YELLOW     = [255,255,0]
COLOUR_RED        = [255,0,0]
COLOUR_BLOCKER    = [255,0,255]
COLOUR_BOMBER_ON  = [255,255,0]
COLOUR_BOMBER_OFF = [200,0,0]
COLOUR_BASE       = [255,255,0]
COLOUR_BRUTE      = [200,0,255]
# wave limits
MAX_BOMBERS   = 10
MAX_BLOCKERS  = 8
MAX_BRUTES    = 2
MAX_WAVE_TIME = 60 # length of wave in seconds
# scores
SCORE_TARGET_HIT  = 250
SCORE_BOMBER_HIT  = 500
SCORE_BRUTE_HIT   = 1000
SCORE_BLOCKER_HIT = -250

# ======================================================================
# setup pygame
# ======================================================================
# set mixer to 512 value to stop buffering causing sound delay
# this must be called before anything else using mixer.pre_init()

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Cannon")
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
clock = pygame.time.Clock()

# ======================================================================
# load images and sounds
# ======================================================================

FILEPATH = pathlib.Path().cwd() 
sound_boom      = pygame.mixer.Sound(str(FILEPATH.joinpath('sounds' ,'boom.ogg')))
sound_big_boom  = pygame.mixer.Sound(str(FILEPATH.joinpath('sounds' ,'big_boom.ogg')))
sound_gunfire   = pygame.mixer.Sound(str(FILEPATH.joinpath('sounds' ,'gunfire.ogg')))
sound_dryfire   = pygame.mixer.Sound(str(FILEPATH.joinpath('sounds' ,'dryfire.ogg')))
sound_blocker   = pygame.mixer.Sound(str(FILEPATH.joinpath('sounds' ,'blocker.ogg')))
sound_base_boom = pygame.mixer.Sound(str(FILEPATH.joinpath('sounds' ,'base_explode.ogg')))

myfont10 = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 10)
myfont20 = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 20)
myfont30 = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 30)
myfont80 = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 80)

SCOREFONT_TARGET_HIT  = myfont20.render(str(SCORE_TARGET_HIT) , 0, COLOUR_YELLOW)
SCOREFONT_BOMBER_HIT  = myfont20.render(str(SCORE_BOMBER_HIT) , 0, COLOUR_YELLOW)
SCOREFONT_BRUTE_HIT   = myfont20.render(str(SCORE_BRUTE_HIT)  , 0, COLOUR_YELLOW)
SCOREFONT_BLOCKER_HIT = myfont20.render(str(SCORE_BLOCKER_HIT), 0, COLOUR_RED)

#=======================================================================
# Score Partical class
#=======================================================================

class ScorePartical():
    
    def __init__(self, pos, angle, speed, image):
        
        self.pos = Vector2(pos.x, pos.y)
        self.vel = Vector2(0, 0)
        self.acc = Vector2(0,0)     
        self.alpha = 255   
        self.acc.setFromAngle(angle)
        self.acc.mult(speed)
        self.image = image
        self.image.set_alpha(self.alpha)
        
    def update(self):
        
        self.vel.add(self.acc)
        self.pos.add(self.vel)
        self.alpha -= abs(self.vel.y)
        self.alpha = max(0,self.alpha)
        self.image.set_alpha(self.alpha)
        
        # gravity hack
        self.vel.y += 0.5
        
    def draw(self):
        
        screen.blit(self.image, (self.pos.x, self.pos.y))
        
    def isOffScreen(self):
        
        return (self.pos.x < 0) or (self.pos.x > SCREEN_WIDTH) or (self.pos.y < 0) or (self.pos.y > SCREEN_HEIGHT)
        
    def isDead(self):
        
        return (self.alpha <= 0) or (self.isOffScreen())


#=======================================================================
# Partical class
#=======================================================================

class Partical():
    
    def __init__(self, pos, angle, speed, size, colour):
        
        self.pos = Vector2(pos.x, pos.y)
        self.vel = Vector2(0, 0)
        self.acc = Vector2(0,0)     
        self.size = size
        self.alpha = 255   
        self.acc.setFromAngle(angle)
        self.acc.mult(speed)
        self.image = pygame.Surface([self.size, self.size])
        self.image.fill(colour)
        self.image.set_alpha(self.alpha)
        
    def update(self):
        
        self.vel.add(self.acc)
        self.pos.add(self.vel)
        self.alpha -= abs(self.vel.y)
        self.alpha = max(0,self.alpha)
        self.image.set_alpha(self.alpha)
        
        # gravity hack
        self.vel.y += 0.2
        
    def draw(self):
        
        screen.blit(self.image, (self.pos.x, self.pos.y))
        
    def isOffScreen(self):
        
        return (self.pos.x < 0) or (self.pos.x > SCREEN_WIDTH) or (self.pos.y < 0) or (self.pos.y > SCREEN_HEIGHT)
        
    def isDead(self):
        
        return (self.alpha <= 0) or (self.isOffScreen())
    

#=======================================================================
# particlesystem class
#=======================================================================

class ParticleSystem():
    
    def __init__(self, x, y, mx = 20):
        
        self.pos = Vector2(x, y)
        self.particles = []
        self.max_particles = mx
        
    def killAll(self):
        
        self.particles = []
        
    def burstDirection(self, angle, spread, colour):
        
        self.killAll()
        for n in range(0, self.max_particles):
            if colour is None:
                c = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
            else:
                c = colour
            # vary the angle a little bit
            angle = (angle + random.uniform(-spread, spread)) % 360
            speed = random.uniform(0.1, 0.7)
            size = random.randint(1, 10)
            p = Partical(self.pos, angle, speed, size, c)
            self.particles.append(p)
            
    def burstCircle(self, colour):
        
        self.killAll()
        step = 360 // self.max_particles
        for n in range(0, self.max_particles):
            if colour is None:
                c = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
            else:
                c = colour
                
            angle = n * step
            speed = random.uniform(0.1, 0.7)
            size = random.randint(1, 14)
            if size < 5 and random.random() > 0.6:
                c = COLOUR_WHITE
            
            p = Partical(self.pos, angle, speed, size, c)
            self.particles.append(p)
    
        
    def scoreBurst(self, scoreimage):
        
        self.killAll()
        step = 360 // self.max_particles
        for n in range(0, self.max_particles):
            angle = n * step
            speed = 0.5
            p = ScorePartical(self.pos, angle, speed, scoreimage)
            self.particles.append(p)
            
    def update(self):
        
        cp = [p for p in self.particles if not p.isDead()]
        self.particles = cp
        for p in self.particles:
            p.update()
            p.draw()
        
    def isDead(self):
        
        return len(self.particles) == 0
        

#=======================================================================
# particlesystemController class
#=======================================================================

class ParticleSystemController():
    
    def __init__(self):
        
        self.systems = []
        
    def spawn(self, x, y, mx):
        
        system = ParticleSystem(x, y, mx)
        self.systems.append(system)
        return system
        
    def spawnBurstDirection(self, x, y, angle, spread, max_particles = 20, colour=None):
        
        system = self.spawn(x, y, max_particles)
        system.burstDirection(angle, spread, colour)
        
    def spawnBurstCircle(self, x, y, max_particles = 20, colour=None):
        
        system = self.spawn(x, y, max_particles)
        system.burstCircle(colour)
        
    def spawnScoreBurst(self, x, y, scoreimage):
        
        system = self.spawn(x, y, 3)
        system.scoreBurst(scoreimage)
        
    def killAll(self):
        
        self.systems = []
    
    def update(self):
        
        cp = [ps for ps in self.systems if not ps.isDead()]
        self.systems = cp
        for s in self.systems:
            s.update()       

        
#=======================================================================
# Star class
#=======================================================================

class Star():
    
    def __init__(self):
        
        self.position = Vector2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        self.velocity = Vector2(0.0, 1 + random.random() * 10)
        self.size = random.randint(1,4)
        self.image = pygame.Surface([self.size, self.size])
        self.rect = self.image.get_rect()
        self.image.fill(COLOUR_STARS)

    def reset(self):
        
        self.position.y = 0
        self.position.x = random.randint(0, SCREEN_WIDTH)
        self.velocity.y = 1 + random.random() * 10
        
    def update(self):
        
        # add a little to vel each frame to make it look a bit 
        # like gravity is pulling it down like rain
        # reset() will set vel back to a baseline
        
        self.velocity.y += 0.02
        self.position.add(self.velocity)
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        
    def draw(self):
        
        screen.blit(self.image, self.rect)


#=======================================================================
# Starfield class
#=======================================================================

class StarField():
    
    def __init__(self):
        
        self.stars = []
        self.max_stars = 40
        
        for i in range(0, self.max_stars):
            star = Star()
            self.stars.append(star)
            
    def update(self):
        
        for star in self.stars:
            star.update()
            
            if star.position.y > SCREEN_HEIGHT:
                star.reset()
                
    def draw(self):
        
        for star in self.stars:
            star.draw()


# ======================================================================
# cannonball class
# ======================================================================
class Cannonball():

    def __init__(self, x, y):
        
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.acc = Vector2(0, 0)
        self.size = 8
        self.mass = 20
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.image = pygame.Surface([self.size, self.size])
        self.image.fill(COLOUR_WHITE)
        self.isflying = False
        self.dead = False
        
    def launch(self, f):
        
        self.applyForce(f)
        self.isflying = True
        
    def applyForce(self, f):
        
        # make a copy to preserve the original vector values
        fcopy = f.getCopy()
        fcopy.div(self.mass)
        self.acc.add(fcopy)
        
    def update(self):
        
        self.vel.add(self.acc)
        self.pos.add(self.vel)
        self.acc.mult(0)
        self.constrain()
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        
    def constrain(self):
        
        if self.pos.y > SCREEN_HEIGHT - self.size:
            self.pos.y = SCREEN_HEIGHT - self.size
            self.vel.mult(0)
            
    def isDead(self):
        
        # return true if ball is on the ground
        return self.pos.y == SCREEN_HEIGHT - self.size or self.dead
        
    def draw(self):
        
        if not self.isDead():
            screen.blit(self.image, self.rect)


# ======================================================================
# cannon class
# ======================================================================

class Cannon():

    def __init__(self, x, y):
        
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.maxballs = 0
        self.balls = None
        self.loadedball = 0
        self.firepower = 150
        
    def load(self, balls):
        
        self.loadedball = 0
        self.balls = balls 
        self.maxballs = len(balls)
        
    def fire(self, mousex, mousey):
    
        f = Vector2(mousex, mousey)
        f.sub(self.pos)
        f.normalise()
        f.mult(self.firepower) 
        self.balls[self.loadedball].launch(f)
        self.loadedball += 1
    
    def update(self):
        
        pass
        
    def draw(self):
        
        pygame.draw.rect(screen,[255,0,255],[self.pos.x,self.pos.y, 10, 10])


# ======================================================================
# target class
# ======================================================================

class Target():

    def __init__(self, x, y, w, h):
        
        self.pos = Vector2(x, y)
        self.vel = Vector2(-0.5 + random.random() * -1.5, 0)
        self.width = w
        self.height = h
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(COLOUR_RED)
        self.dead = False
        
    def isDead(self):
        
        return self.dead == True
        
    def update(self):
                
        self.pos.add(self.vel)
        if self.pos.x < 0:
            self.pos.x = SCREEN_WIDTH
            
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        
    def draw(self):
        
        screen.blit(self.image, self.rect)

# ======================================================================
# blocker class
# ======================================================================

class Blocker():

    def __init__(self, x, y, w, h):
        
        self.pos = Vector2(x, y)
        self.vel = Vector2(-1 + random.random() * -0.5, 0)
        self.width = w
        self.height = h
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(COLOUR_BLOCKER)
        self.dead = False
        
    def isDead(self):
        
        return self.dead == True
        
    def update(self):
        
        self.pos.add(self.vel)
        if self.pos.x < 0:
            self.pos.x = SCREEN_WIDTH
            
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        
    def draw(self):
        
        screen.blit(self.image, self.rect)
        
# ======================================================================
# bomber class
# ======================================================================

class Bomber():

    def __init__(self, x, y, w, h, vy):
        
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, vy)
        self.width = w
        self.height = h
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(COLOUR_BOMBER_ON)
        self.dead = False
        self.lastflash = 0
        self.thisframe = 0
        self.flash = False
        self.angle = random.randint(0,360)
        
    def isDead(self):
        
        return self.dead == True
        
    def update(self):
        
        self.angle += 1
        if self.angle > 360:
            self.angle = 0
        
        self.thisframe += 1
        if self.thisframe - self.lastflash > 10:
            self.flash = not self.flash
            self.lastflash = self.thisframe
        
        if self.flash:
            self.image.fill(COLOUR_BOMBER_ON)
        else:
            self.image.fill(COLOUR_BOMBER_OFF)
        
        self.pos.add(self.vel)
        self.dead = self.pos.y > SCREEN_HEIGHT
        
        offset = math.cos(math.radians(self.angle))
        self.pos.x += offset
        
        self.rect.x = self.pos.x 
        self.rect.y = self.pos.y
        
    def draw(self):
        
        screen.blit(self.image, self.rect)
        
# ======================================================================
# brute class
# ======================================================================

class Brute():

    def __init__(self, x, y, tx, ty):
        
        self.pos    = Vector2(x, y)
        self.vel    = Vector2(0, 0)
        self.width  = 20
        self.height = 20
        self.rect   = pygame.Rect(x, y, self.width, self.height)
        self.image  = pygame.Surface([self.width, self.height])
        self.dead   = False
        self.angle  = random.randint(0,360)
        self.radius = 1
        self.radius_step = 0.1
        self.image.fill(COLOUR_BRUTE)
        
        # get a vector to carry us to the target
        tv = Vector2(tx,ty)
        tv.sub(self.pos)
        tv.normalise()
        tv.mult(0.6)
        self.vel.set(tv)
        
    def isDead(self):
        
        return self.dead == True
        
    def update(self):
        
        self.radius += self.radius_step
        if self.radius < 0 or self.radius > 40:
            self.radius_step = -self.radius_step
        
        self.angle += 1
        if self.angle > 360:
            self.angle = 0
            
        xoff = math.cos(math.radians(self.angle)) 
        yoff = math.sin(math.radians(self.angle)) 
        
        self.pos.add(self.vel)
        self.dead = self.pos.y > SCREEN_HEIGHT or self.pos.y < 0 or self.pos.x < 0 or self.pos.x > SCREEN_WIDTH

        self.rect.x = self.pos.x + (xoff * self.radius)
        self.rect.y = self.pos.y + (yoff * self.radius)
        
    def draw(self):
        
        screen.blit(self.image, self.rect)


# ======================================================================
# base class
# ======================================================================

class Base():

    def __init__(self, x, y, w, h):
        
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.width = w
        self.height = h
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(COLOUR_BASE)
        self.dead = False
        
    def isDead(self):
        
        return self.dead == True
        
    def update(self):
        
        self.pos.add(self.vel)
        if self.pos.x < 0:
            self.pos.x = SCREEN_WIDTH
            
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        
    def draw(self):
        
        screen.blit(self.image, self.rect)
        
# ======================================================================
# scoreboard class
# ======================================================================

class Scoreboard():
    
    def __init__(self):
        
        self.score = 0
        self.targetscore = 0 # lerp to this
        self.needTableUpdate = True
        
        try:
            self.highscores = pickle.load(open("highscores.pkl", "rb"))
        except:
            self.highscores = [i * 250 for i in range(0, 10)]
            
        self.highscores.sort(reverse=True)
        
    def add(self, n):
        
        self.targetscore += n
        
    def reset(self):
        
        self.score = 0
        self.targetscore = 0
        self.needTableUpdate = True
        
    def finish(self):
        
        # in case the lerping didn't get time to finish
        self.score = self.targetscore
        
        if self.needTableUpdate:
            if self.score > min(self.highscores):
                self.highscores.append(self.score)
                self.highscores.sort(reverse=True)
                self.highscores.pop()
                self.save()
                self.needTableUpdate = False
    
    def drawHighScoreTable(self):
            
        alpha = 200
        xoff = 760
        yoff = 40
        highlight_done = False
        
        textsurf = myfont30.render('HIGHSCORES.', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (xoff,yoff))
        
        yoff += 40
        
        for i, line in enumerate(self.highscores):
            
            alpha -= 14
            msg = '{:02d} ... {}'.format(i+1, line)
            textsurf = myfont30.render(msg, 0, COLOUR_RED)
            
            if line == self.score and not highlight_done:
                textsurf.set_alpha(255)
                highlight_done = True
            else:
                textsurf.set_alpha(alpha)
                
            screen.blit(textsurf, (xoff, yoff + (i * 40)))
        
    def save(self):
        
        pickle.dump(self.highscores, open( "highscores.pkl", "wb" ))
        
    def update(self):
        
        if self.score != self.targetscore:
            self.score = self.lerp(self.score, self.targetscore, 0.02)
        
    def lerp(self, mn, mx, norm):
    
        return math.ceil(((mx - mn) * norm + mn))
        
    def draw(self, fired, maxballs, wavenumber, seconds):
        
        msg = 'WAVE {} ::: FIRED {}/{} ::: SCORE {} ::: {}'.format(wavenumber, fired, maxballs, self.score, seconds)
        textsurf = myfont30.render(msg, 0, COLOUR_RED)
        textsurf.set_alpha(160)
        screen.blit(textsurf, (40,20))

# ======================================================================
# reticule/crosshair class
# ======================================================================

class Reticule():
    
    def __init__(self):
        
        self.pos = Vector2(0,0)
        self.text_offset = 32
        self.xoff = 0
        
    def update(self, mousex, mousey):
        
        self.pos.x = mousex
        self.pos.y = mousey
        
    def microUpdate(self, value):
        
        self.xoff += value
        
    def draw(self):
        
        pygame.draw.rect(screen,[255,255,255],[self.pos.x,self.pos.y, 2, 2])
        pygame.draw.rect(screen,[200,200,200],[self.pos.x-9,self.pos.y-9, 20, 20], 1)
        pygame.draw.line(screen, [0,0,100], [10,550], [self.pos.x,self.pos.y], 2)

    
# ======================================================================
# game class
# ======================================================================

class Game():

    def __init__(self):
        
        self.gamemode          = GAME_MODE_LIVE
        self.gamestate         = GAME_STATE_INTRO
        self.slowmotion        = False
        self.fps               = 60
        self.replay_length     = 0
        self.gamestate_delay   = 0
        self.current_tick      = 0
        self.wave_start_tick   = 0
        self.wave_seconds      = 60
        self.wave_number       = 0
        self.maxballs          = 50
        self.shots_fired       = 0
        self.shots_fired_total = 0
        
        self.cannon     = Cannon(10,550)
        self.reticule   = Reticule()
        self.starfield  = StarField()
        self.psc        = ParticleSystemController()
        self.scoreboard = Scoreboard()
        
        self.balls     = []
        self.bases     = []
        self.targets   = []
        self.blockers  = []
        self.bombers   = []
        self.brutes    = []
        self.recording = []
        
        self.gravity = Vector2(0,0.3)
        
        self.startGame()

    def toggleSlowMotion(self):
        
        self.slowmotion = not self.slowmotion

    def getDrag(self, ball):
        
        c = 0.012
        speed = ball.vel.mag()
        dragMag = c * speed * speed
        drag = ball.vel.getCopy()
        drag.mult(-1)
        drag.normalise()
        drag.mult(dragMag)
        return drag
        
    def reload(self):
        
        self.shots_fired_total += self.shots_fired
        self.shots_fired = 0
        self.balls = [Cannonball(self.cannon.pos.x, self.cannon.pos.y) for i in range(0, self.maxballs)]
        self.cannon.load(self.balls)
       
    def startReplay(self):
        
        self.gamemode = GAME_MODE_REPLAY
        self.replay_length = len(self.recording)
        self.startGame()
        self.gamestate = GAME_STATE_IN_PROGRESS   
        
    def startGame(self):
        
        self.thisframe = 0
        self.current_tick = 0
        
        self.wave_number = 0
        self.shots_fired_total = 0
        self.scoreboard.reset()
        self.psc.killAll()
        
        self.bases = []
        for x in range(0, 2):
            b = Base(400 + x * 300, 580, 150, 10)
            self.bases.append(b)
        for y in range(0, 2):
            b = Base(10, 20 + y * 200, 10, 150)
            self.bases.append(b)
            
        self.spawnWave()
        
    def clearOldWave(self):
        
        self.targets  = []
        self.blockers = []
        self.bombers  = []
        self.brutes   = []

    def spawnWave(self):
        
        random.seed(1)
        self.clearOldWave()
        self.reload()
        self.wave_start_tick = self.current_tick
        self.wave_seconds = MAX_WAVE_TIME
        self.wave_number += 1
        
        for x in range(0, self.wave_number):
            t = Target(random.randint(1000, 1800), random.randint(10, SCREEN_HEIGHT-100), 20, 40)
            self.targets.append(t)

        for x in range(0, min(self.wave_number, MAX_BLOCKERS)):
            b = Blocker(random.randint(1000, 1800), random.randint(10, SCREEN_HEIGHT-100), 3, 20)
            self.blockers.append(b)
            
        for x in range(0, min(self.wave_number, MAX_BOMBERS)):
            b = Bomber(random.randint(200, SCREEN_WIDTH-100), 0, 24, 12, 0.1 + (random.random() * 0.5))
            self.bombers.append(b)
            
        # if only 1 base remains, spawn a 'brute' that is hard to hit and moves directly towards the base
        # this will stop the game from getting easy when only one base is left.
        
        if len(self.bases) == 1:
            tx = self.bases[0].pos.x
            ty = self.bases[0].pos.y
            
            for x in range(0, min(self.wave_number, MAX_BRUTES)):
                b = Brute(random.randrange(SCREEN_WIDTH-600, SCREEN_WIDTH-50), random.randrange(100, 200), tx, ty)
                self.brutes.append(b)

    def checkCollisions(self):

        # idea:
        # always do the outer loop being the one with likely the least amount.
        # it will be more efficient.
        # eg 40 balls in the air and no brutes, if balls on outer loop 40 loops are done and wasted
        # if brutes were outer loop, no checks at all would be needed
        
        # do brute collisions
        for brute in self.brutes:
            for base in self.bases:
                if brute.rect.colliderect(base.rect):
                    brute.dead = True
                    base.dead  = True
                    self.psc.spawnBurstDirection(brute.pos.x, brute.pos.y, 270, 2, 50)
                    sound_base_boom.play()
        
        for brute in self.brutes:
            for ball in self.balls:
                if brute.rect.colliderect(ball.rect):
                    brute.dead = True
                    ball.dead  = True
                    self.scoreboard.add(SCORE_BRUTE_HIT)
                    self.psc.spawnBurstDirection(ball.pos.x, ball.pos.y, 270, 2, 50)
                    self.psc.spawnScoreBurst(ball.pos.x, ball.pos.y,SCOREFONT_BRUTE_HIT)
                    sound_big_boom.play()
        
        for ball in self.balls:
            for base in self.bases:
                if ball.rect.colliderect(base.rect):
                    base.dead = True
                    ball.dead = True
                    self.psc.spawnBurstDirection(ball.pos.x, ball.pos.y, 270, 2, 100)
                    sound_base_boom.play()
                    
        for target in self.targets:
            for base in self.bases:
                if target.rect.colliderect(base.rect):
                    base.dead = True
                    target.dead = True
                    self.psc.spawnBurstCircle(target.pos.x, target.pos.y, 50, COLOUR_YELLOW)
                    sound_base_boom.play()
        
        for bomber in self.bombers:
            for base in self.bases:
                if bomber.rect.colliderect(base.rect):
                    base.dead = True
                    bomber.dead = True
                    self.psc.spawnBurstDirection(bomber.pos.x, bomber.pos.y, 270, 20, 200)
                    sound_base_boom.play()
                    
        for bomber in self.bombers:
            for ball in self.balls:
                if bomber.rect.colliderect(ball.rect):
                    bomber.dead = True
                    ball.dead = True
                    self.scoreboard.add(SCORE_BOMBER_HIT)
                    self.psc.spawnBurstDirection(ball.pos.x, ball.pos.y, 270, 20, 50, COLOUR_YELLOW)
                    self.psc.spawnScoreBurst(ball.pos.x, ball.pos.y,SCOREFONT_BOMBER_HIT)
                    sound_big_boom.play()
                    
        for blocker in self.blockers:
            for ball in self.balls:
                if blocker.rect.colliderect(ball.rect):
                    if ball.vel.x > 0: #ball hit from the left
                        ball.pos.x -= 4
                    else:
                        ball.pos.x += 4 # hit was from the right
                    ball.vel.x = -ball.vel.x
                    self.scoreboard.add(SCORE_BLOCKER_HIT)
                    self.psc.spawnScoreBurst(ball.pos.x, ball.pos.y,SCOREFONT_BLOCKER_HIT)
                    sound_blocker.play()
 
        for target in self.targets:
            for ball in self.balls:
                if not target.isDead() and target.rect.colliderect(ball.rect):
                    target.dead = True
                    ball.dead = True
                    self.scoreboard.add(SCORE_TARGET_HIT)
                    boomsize = random.randint(5, 30)
                    self.psc.spawnBurstCircle(ball.pos.x, ball.pos.y, boomsize, COLOUR_RED)
                    self.psc.spawnScoreBurst(ball.pos.x, ball.pos.y,SCOREFONT_TARGET_HIT)
                    if boomsize > 20:
                        sound_big_boom.play()
                    else:
                        sound_boom.play()
                    
        tc = [t for t in self.targets if not t.isDead()]
        self.targets = tc
        
        bc = [b for b in self.balls if not b.isDead()]
        self.balls = bc
        
        bl = [b for b in self.bombers if not b.isDead()]
        self.bombers = bl
        
        ba = [b for b in self.bases if not b.isDead()]
        self.bases = ba
        
        br = [b for b in self.brutes if not b.isDead()]
        self.brutes = br
        
    def fireCannon(self, mx, my):
        
        if self.shots_fired < self.maxballs:
            self.cannon.fire(mx, my)
            sound_gunfire.play()
            self.shots_fired += 1
        else:
            sound_dryfire.play()

    def switchGamestate(self):
        
        # handles when spacebar is pressed
        if self.gamestate in [GAME_STATE_INTRO, GAME_STATE_OVER] or self.gamemode == GAME_MODE_REPLAY:
            self.gamemode = GAME_MODE_LIVE
            self.startGame()
            self.gamestate = GAME_STATE_IN_PROGRESS
            
    def drawIntroScreen(self):
        
        textsurf = myfont80.render('CANNON', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,20))
        textsurf = myfont30.render('press spacebar!', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,540))
        self.scoreboard.drawHighScoreTable()
        
    def drawLastBaseLost(self):
        
        self.gamestate_delay += 1
        if self.gamestate_delay > self.fps * 4:
            self.gamestate = GAME_STATE_OVER
            self.gamestate_delay = 0
        
    def drawGameOver(self):
        
        textsurf = myfont80.render('DEDZ !!!', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,20))
        
        textsurf = myfont30.render('You Scored...{}'.format(self.scoreboard.score), 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,160))
        
        textsurf = myfont30.render('R = View Replay.', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20, 480))
        
        textsurf = myfont30.render('Spacebar = Play Again.', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20, 540))
        
        self.scoreboard.drawHighScoreTable()
            
    def draw(self, mousex, mousey, click):
        
        if self.gamestate == GAME_STATE_INTRO:
            
            self.drawIntroScreen()
            
        elif self.gamestate == GAME_STATE_IN_PROGRESS:
            
            self.current_tick += 1
            
            self.wave_seconds = MAX_WAVE_TIME - (self.current_tick - self.wave_start_tick) // 60
            
            self.reticule.update(mousex, mousey)
            
            if click:
                self.fireCannon(mousex, mousey)
                
            self.scoreboard.update()
            self.starfield.update()
            self.cannon.update()
            self.psc.update()
            
            for ball in self.balls:
                if ball.isflying:
                    ball.applyForce(self.gravity)
                    ball.applyForce(self.getDrag(ball))
                ball.update()
                
            for target in self.targets:
                target.update()
                
            for blocker in self.blockers:
                blocker.update()
                
            for bomber in self.bombers:
                bomber.update()
                
            for base in self.bases:
                base.update()
                
            for brute in self.brutes:
                brute.update()
                
            self.checkCollisions()
            
            self.starfield.draw()
            self.cannon.draw()
            self.reticule.draw()
            self.scoreboard.draw(self.shots_fired, self.maxballs, self.wave_number, self.wave_seconds)
            
            for target in self.targets:
                target.draw()
                
            for blocker in self.blockers:
                blocker.draw()
                
            for bomber in self.bombers:
                bomber.draw()
                
            for brute in self.brutes:
                brute.draw()
                
            for ball in self.balls:
                ball.draw()
                
            for base in self.bases:
                base.draw()
        
        elif self.gamestate == GAME_STATE_WAVE_OVER:
            
            pass
            
        elif self.gamestate == GAME_STATE_LAST_BASE_LOST:
            
            self.psc.update()
            self.drawLastBaseLost()            
            
        elif self.gamestate == GAME_STATE_OVER:
            
            self.drawGameOver()
            self.scoreboard.finish()         
            
    def run(self):
        
        done = False
        
        while not done:
            
            if self.slowmotion:
                pygame.time.wait(50)
            
            if len(self.bases) > 0:
                if len(self.targets) == 0 or self.wave_seconds == 0:
                    self.spawnWave()
            else:
                if self.gamestate == GAME_STATE_IN_PROGRESS:
                    self.gamestate = GAME_STATE_LAST_BASE_LOST
            
            if self.gamemode == GAME_MODE_LIVE:
                mousex, mousey = pygame.mouse.get_pos()
                
            click = False
    
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT:  
                    done = True
                    
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_ESCAPE):
                        done = True
                    elif (event.key == pygame.K_SPACE):
                        game.switchGamestate()
                    elif (event.key == pygame.K_r):
                        self.startReplay()
                    elif (event.key == pygame.K_s):
                        self.toggleSlowMotion()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # left click
                        click = True
                        
            if self.gamestate == GAME_STATE_IN_PROGRESS:
                if self.gamemode == GAME_MODE_LIVE: 
                    self.recording.append( (mousex, mousey, click) )
                else:
                    # game is showing a replay of last game
                    if self.thisframe < self.replay_length:
                        mousex, mousey, click = self.recording[self.thisframe]
                        self.thisframe += 1
                
            screen.fill(COLOUR_BLACK)
            game.draw(mousex, mousey, click)
            clock.tick(self.fps)
            pygame.display.flip()
        
game = Game()
game.run()
pygame.quit()
