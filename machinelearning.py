import pygame
import math
from pygame.locals import *
 
#-----------------------------------------------------VARIABLES-----------------------------------------------------
w, h = 960, 720 # Set dimensions of game GUI
fps   = 60  # frame rate
ani   = 4   # animation cycles
running = True # Set running and moving values

#-----------------------------------------------------OBJECTS-------------------------------------------------------
class Car(pygame.sprite.Sprite):
    def __init__(self, x, y, rotations=360):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.min_angle = (360 / rotations)
        
        img = pygame.image.load('res/car.png').convert_alpha()
        
        for i in range(rotations):
            rotated_image = pygame.transform.rotozoom(img, 360 - 90 - (i * self.min_angle), 1)
            self.images.append(rotated_image)
        
        self.min_angle = math.radians(self.min_angle)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.reversing = False
        self.heading = 0
        self.speed = 0
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(x, y)
        
    def turn(self, angle_degree):
        if abs(self.speed) > 1:
            self.heading += math.radians(angle_degree)
        image_index = int(self.heading / self.min_angle) % len(self.images)
        
        if(self.image != self.images[image_index]):
            x,y = self.rect.center
            self.image = self.images[image_index]
            self.rect = self.image.get_rect()
            self.rect.center = (x,y)
            
    def accelerate(self, amount):
            self.speed += amount
            
            if self.speed > 3:
                self.speed = 3
            
    def brake(self):
        self.speed /= 2
        if abs(self.speed) < 0.1:
            self.speed = 0
            
    def reverse(self, amount):
        self.speed -= amount
        
        if self.speed < -3:
            self.speed = -3
        
    def update(self):
        self.velocity.from_polar((self.speed, math.degrees(self.heading)))
        self.position += self.velocity
        self.rect.center = (round(self.position[0]), round(self.position[1]))
        
        if self.speed > 0:
            self.speed -= 0.01
        elif self.speed < 0:
            self.speed += 0.01

#-----------------------------------------------------FUNCTIONS-----------------------------------------------------
def Init(): 
    pygame.init()
    car_list.add(player)
    
def InputPolling():
    pressed = pygame.key.get_pressed()
    
    if pressed[pygame.K_UP]:
            player.accelerate(0.1)
    elif pressed[pygame.K_DOWN]:
            player.reverse(0.05)
            
    if pressed[pygame.K_LEFT]:
            player.turn(-1.8)
    elif pressed[pygame.K_RIGHT]:
            player.turn(1.8)
            
    if pressed[pygame.K_SPACE]:
            player.brake()
        
        

def Update():
    car_list.update()
    
def Render():
    screen.blit(resized_background, (0,0))
    car_list.draw(screen)
    pygame.display.update()

def Quit():
    pygame.quit()

#-----------------------------------------------------SET UP--------------------------------------------------------
clock = pygame.time.Clock() # Internal Clock
screen = pygame.display.set_mode((w, h))
backdrop = pygame.image.load('res/track_1.png')
resized_background = pygame.transform.scale(backdrop, (w, h)) 

player = Car(w/2, h/2)
car_list = pygame.sprite.Group()

#-----------------------------------------------------MAIN LOOP-----------------------------------------------------
Init()

while running:
     
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
    InputPolling()
    Update()
    Render()
    clock.tick(fps)
    
Quit()
