import pygame
import math
import random
import pathlib
from vector import Vector2
  
# ======================================================================
# constants to help code readability
# ======================================================================

FPS = 60
GAME_STATE_INTRO          = 0
GAME_STATE_IN_PROGRESS    = 1
GAME_STATE_WAVE_OVER      = 2
GAME_STATE_LAST_BASE_LOST = 3
GAME_STATE_OVER           = 4
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
ORIGINX = SCREEN_WIDTH // 2
ORIGINY = SCREEN_HEIGHT // 2
COLOUR_BLACK   = [0,0,0]
COLOUR_WHITE   = [255,255,255]
COLOUR_STARS   = [100,50,255]
COLOUR_YELLOW  = [255,255,0]
COLOUR_RED     = [255,0,0]
COLOUR_BLOCKER = [255,0,255]
COLOUR_BOMBER_ON = [255,255,0]
COLOUR_BOMBER_OFF = [200,0,0]
COLOUR_BASE       = [255,255,0]
MAX_BOMBERS = 10
MAX_BLOCKERS = 8
MAX_WAVE_TIME = 60 # length of wave in seconds

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

myfont   = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 20)
myfont10 = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 10)
myfonttitle = pygame.font.Font(str(FILEPATH.joinpath('assets' ,'digitalix.ttf')), 80)

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
        self.vel.y += 0.3
        
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
        self.size = 10
        self.mass = 20
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.image = pygame.Surface([self.size, self.size])
        self.image.fill(COLOUR_YELLOW)
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
        self.vel = Vector2(-1 + random.random() * -1.5, 0)
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
        
    def isDead(self):
        
        return self.dead == True
        
    def update(self):
        
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
        
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        
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
        
    def add(self, n):
        
        self.targetscore += n
        
    def reset(self):
        
        self.score = 0
        self.targetscore = 0
        
    def update(self):
        
        if self.score < self.targetscore:
            self.score = self.lerp(self.score, self.targetscore, 0.02)
        
    def lerp(self, mn, mx, norm):
    
        return math.ceil(((mx - mn) * norm + mn))
        
    def draw(self, fired, maxballs, wavenumber, seconds=60):
        
        msg = 'WAVE {} ::: FIRED {}/{} ::: SCORE {} ::: {}'.format(wavenumber, fired, maxballs, self.score, seconds)
        textsurf = myfont.render(msg, 0, COLOUR_RED)
        textsurf.set_alpha(160)
        screen.blit(textsurf, (20,20))
        


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
        
        pygame.draw.rect(screen,[255,255,255],[self.pos.x,self.pos.y, 4, 4])
        
        msg = '{}/{}'.format(self.pos.x + self.xoff, self.pos.y)
        text = myfont10.render(msg, 0, COLOUR_RED)
        text.set_alpha(150)
        screen.blit(text, (self.pos.x + self.text_offset, self.pos.y + self.text_offset))
    
# ======================================================================
# game class
# ======================================================================

class Game():

    def __init__(self):
        
        self.gamestate = GAME_STATE_INTRO
        self.gamestate_delay = 0
        self.wave_start_tick = 0
        self.wave_seconds = 60
        self.wave_number = 0
        self.maxballs = 50
        self.shots_fired = 0
        self.shots_fired_total = 0
        self.cannon = Cannon(10,550)
        self.reticule = Reticule()
        self.starfield = StarField()
        self.psc = ParticleSystemController()
        self.scoreboard = Scoreboard()
        self.balls    = []
        self.bases    = []
        self.targets  = []
        self.blockers = []
        self.bombers  = []
        
        self.gravity = Vector2(0,0.3)
        self.startGame()

    def getFriction(self, ball):
        
        # c is the coefficient of drag
        # ie how draggy the surface is. ice = 0.01 tarmac = 0.9
        # i could vary c according to the position of the ball
        c = 1.2
        v = ball.vel.getCopy() # we are a copy of the ball velocity
        v.mult(-1) # this reverses the direction of force
        v.normalise()
        v.mult(c)
        return v
    
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
        
    def startGame(self):
        
        self.wave_number = 0
        self.shots_fired_total = 0
        self.scoreboard.reset()
        self.psc.killAll()
        
        self.bases = []
        for x in range(0, 3):
            b = Base(400 + x * 150, 580, 50, 10)
            self.bases.append(b)
            
        self.spawnWave()

    def spawnWave(self):
        
        self.reload()
        self.wave_start_tick = pygame.time.get_ticks() 
        self.wave_seconds = MAX_WAVE_TIME
        self.wave_number += 1
        
        self.targets = []
        for x in range(0, self.wave_number):
            t = Target(random.randint(1000, 1400), random.randint(10, SCREEN_HEIGHT-100), 12, 30)
            self.targets.append(t)

        self.blockers = []
        for x in range(0, min(self.wave_number, MAX_BLOCKERS)):
            b = Blocker(random.randint(1000, 1400), random.randint(10, SCREEN_HEIGHT-100), 3, 40)
            self.blockers.append(b)
            
        self.bombers = []
        for x in range(0, min(self.wave_number, MAX_BOMBERS)):
            b = Bomber(random.randint(300, 800), 0, 12, 6, 0.4 + (random.random() * 0.4))
            self.bombers.append(b)

    def checkCollisions(self):
        
        for ball in self.balls:
            for base in self.bases:
                if ball.rect.colliderect(base.rect):
                    base.dead = True
                    ball.dead = True
                    self.psc.spawnBurstDirection(ball.pos.x, ball.pos.y, 270, 2, 100)
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
                    self.scoreboard.add(1000)
                    self.psc.spawnBurstDirection(bomber.pos.x, bomber.pos.y, 270, 20, 50, COLOUR_YELLOW)
                    sound_big_boom.play()
                    
        for blocker in self.blockers:
            for ball in self.balls:
                if blocker.rect.colliderect(ball.rect):
                    if ball.vel.x > 0: #ball hit from the left
                        ball.pos.x -= 4
                    else:
                        ball.pos.x += 4 # hit was from the right
                    ball.vel.x = -ball.vel.x
                    sound_blocker.play()
 
        for target in self.targets:
            for ball in self.balls:
                if not target.isDead() and target.rect.colliderect(ball.rect):
                    target.dead = True
                    ball.dead = True
                    self.scoreboard.add(250)
                    boomsize = random.randint(5, 50)
                    self.psc.spawnBurstCircle(target.pos.x, target.pos.y, boomsize, COLOUR_RED)
                    if boomsize > 35:
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
        
            
    def fireCannon(self, mx, my):
        
        if self.shots_fired < self.maxballs:
            self.cannon.fire(mx, my)
            sound_gunfire.play()
            self.shots_fired += 1
        else:
            sound_dryfire.play()

    def switchGamestate(self):
        
        if self.gamestate == GAME_STATE_INTRO or self.gamestate == GAME_STATE_OVER:
            self.startGame()
            self.gamestate = GAME_STATE_IN_PROGRESS
      
    def drawIntroScreen(self):
        
        textsurf = myfonttitle.render('CANNON', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,20))
        textsurf = myfont.render('press spacebar to start !', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,200))
        
    def drawLastBaseLost(self):
        
        self.gamestate_delay += 1
        if self.gamestate_delay > FPS * 4:
            self.gamestate = GAME_STATE_OVER
            self.gamestate_delay = 0
        
    def drawGameOver(self):
        
        textsurf = myfonttitle.render('YOU IS DEDZ !!!', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,20))
        
        textsurf = myfont.render('You Scored ::: {}'.format(self.scoreboard.score), 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,200))
        
        textsurf = myfont.render('press spacebar to play again !', 0, COLOUR_RED)
        textsurf.set_alpha(255)
        screen.blit(textsurf, (20,400))
            
    def draw(self, mousex, mousey):
        
        if self.gamestate == GAME_STATE_INTRO:
            
            self.drawIntroScreen()
            
        elif self.gamestate == GAME_STATE_IN_PROGRESS:
            
            self.wave_seconds = MAX_WAVE_TIME - (pygame.time.get_ticks()-self.wave_start_tick) // 1000
            
            self.reticule.update(mousex, mousey)
            self.reticule.draw()
            
            self.scoreboard.update()
            self.scoreboard.draw(self.shots_fired, self.maxballs, self.wave_number, self.wave_seconds)
            
            self.starfield.update()
            self.starfield.draw()
    
            self.cannon.update()
            self.cannon.draw()
            
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
                
            self.checkCollisions()
            
            for target in self.targets:
                target.draw()
                
            for blocker in self.blockers:
                blocker.draw()
                
            for bomber in self.bombers:
                bomber.draw()
                
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
            
        
        
    def run(self):
        
        done = False
        
        while not done:
            
            if len(self.bases) > 0:
                if len(self.targets) == 0 or self.wave_seconds == 0:
                    self.spawnWave()
            else:
                if self.gamestate == GAME_STATE_IN_PROGRESS:
                    self.gamestate = GAME_STATE_LAST_BASE_LOST
            
            mousex, mousey = pygame.mouse.get_pos()
    
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT:  
                    done = True
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_ESCAPE):
                        done = True
                    elif (event.key == pygame.K_SPACE):
                        game.switchGamestate()
                    elif (event.key == pygame.K_UP):
                        pass
                    elif (event.key == pygame.K_DOWN):
                        pass
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    
                    if event.button == 1: # left click
                        self.fireCannon(mousex, mousey)
                    
                    if event.button == 4: # scroll wheel up 
                        
                        self.reticule.microUpdate(-1)
                        print('scroll up adjust aim tiny bit up')
                        
                    if event.button == 5: # scroll wheel down
                        
                        self.reticule.microUpdate(1)
                        print('scroll down') 
                        
            screen.fill(COLOUR_BLACK)
            game.draw(mousex, mousey)
            clock.tick(FPS)
            pygame.display.flip()
        
game = Game()
game.run()
pygame.quit()
