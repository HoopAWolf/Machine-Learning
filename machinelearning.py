import pygame
import neat
import math
import os
import sys
from pygame.locals import *
 
#-----------------------------------------------------VARIABLES-----------------------------------------------------
w, h = 960, 720 # Set dimensions of game GUI
fps   = 60  # frame rate
ani   = 4   # animation cycles
current_generation = 0 # Generation counter
BORDER_COLOR = (48, 160, 0, 255) # Set wall color
CAR_SIZE_HEIGHT = 44

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
        
        self.alive = True
        self.min_angle = math.radians(self.min_angle)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.reversing = False
        self.heading = 0
        self.speed = 0
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(x, y)
        self.distance_travelled = 0
        self. time_taken = 0
        
        self.sensors = []
        self.drawing_sensors = []
        
    def turn(self, angle_degree):
        if abs(self.speed) > 0.2:
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
        self.speed *= 0.5
        if abs(self.speed) < 0.1:
            self.speed = 0
            
    def reverse(self, amount):
        self.speed -= amount
        
        if self.speed < -3:
            self.speed = -3
        
    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break
            
    def check_sensor(self, degree, game_map):
        length = 0
        x = int(self.rect.center[0] + math.cos(math.radians(360 - (math.degrees(self.heading) + degree))) * length)
        y = int(self.rect.center[1] + math.sin(math.radians(360 - (math.degrees(self.heading) + degree))) * length)
        
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length += 1
            x = int(self.rect.center[0] + math.cos(math.radians((math.degrees(self.heading) + degree))) * length)
            y = int(self.rect.center[1] + math.sin(math.radians( (math.degrees(self.heading) + degree))) * length)
            
        dist = int(math.sqrt(math.pow(x - self.rect.center[0], 2) + math.pow(y - self.rect.center[1], 2)))
        self.sensors.append([(x, y), dist])
        
    def get_reward(self):
        return (self.distance_travelled / (CAR_SIZE_HEIGHT * 0.5)) * 1 if self.speed > 2 else -1
        
    def get_distance_to_border_data(self):
        sensors = self.sensors
        values = [0, 0, 0, 0, 0]
        
        for i, sensor in enumerate(sensors):
            values[i] = int(sensor[1] * 0.03)
        
        return values
    
    def update(self, game_map):
        if self.alive:
            self.velocity.from_polar((self.speed, math.degrees(self.heading)))
            self.position += self.velocity
            self.rect.center = (round(self.position[0]), round(self.position[1]))
            self.distance_travelled += self.speed
            self.time_taken += 1
            if self.speed > 0:
                self.speed -= 0.01
            elif self.speed < 0:
                self.speed += 0.01
            
        length = 0.5 * CAR_SIZE_HEIGHT
        left_top = [self.rect.center[0] + math.cos(math.radians((math.degrees(self.heading) + 30))) * length, self.rect.center[1] + math.sin(math.radians((math.degrees(self.heading) + 30))) * length]
        right_top = [self.rect.center[0] + math.cos(math.radians((math.degrees(self.heading) + 150))) * length, self.rect.center[1] + math.sin(math.radians((math.degrees(self.heading) + 150))) * length]
        left_bottom = [self.rect.center[0] + math.cos(math.radians((math.degrees(self.heading) + 210))) * length, self.rect.center[1] + math.sin(math.radians((math.degrees(self.heading) + 210))) * length]
        right_bottom = [self.rect.center[0] + math.cos(math.radians((math.degrees(self.heading) + 330))) * length, self.rect.center[1] + math.sin(math.radians((math.degrees(self.heading) + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]
        
        self.check_collision(game_map)
        self.sensors.clear()
        for degree in range(-90, 120, 45):
            self.check_sensor(degree, game_map)
    
    def draw_sensors(self, screen):
        for sensor in self.sensors:
            position = sensor[0]
            pygame.draw.line(screen, (0, 255, 0) if self.alive else (255, 0, 0), self.rect.center, position, 1)
            

#-----------------------------------------------------FUNCTIONS-----------------------------------------------------
def Init(): 
    global text_font
    
    pygame.init()
    text_font = pygame.font.SysFont(None, 20)
    
    population.add_reporter(neat.StdOutReporter(True))
    
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

def InputSimulation(ais, neural_networks):             
    for i, ai in enumerate(ais):
        if ai.alive:            
            output = neural_networks[i].activate(ai.get_distance_to_border_data())
            choice = output.index(max(output))
        
            if choice == 0:
                ai.turn(1.8) # Turn left
            elif choice == 1:
                ai.turn(-1.8) # Turn right
            elif choice == 2:
                ai.reverse(0.05) # Slow down
            else:
                ai.accelerate(0.1) # Speed up
     
def Update():
    car_list.update(resized_background)
    
def UpdateSimulation(ais, genomes, still_alive):
    car_list.update(resized_background)
    
    still_alive[0] = 0
    for i, ai in enumerate(ais):
        if ai.alive:
            still_alive[0] += 1
            genomes[i][1].fitness += ai.get_reward()
        
    
def Render():
    screen.blit(resized_background, (0,0))
    car_list.draw(screen)
    pygame.display.update()
    
def RenderSimulation(ais, genomes):
    screen.blit(resized_background, (0,0))
    car_list.draw(screen)
    
    for i, ai in enumerate(ais):
        if ai.alive:
            ai.draw_sensors(screen)
        text = text_font.render(str(int(genomes[i][1].fitness)), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = [ai.rect.center[0], ai.rect.center[1] + 15]
        screen.blit(text, text_rect)
    
    pygame.display.update()

def MainLoop():
    running = True
    counter = 0
    car_list.add(player)
    
    while running:
         
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
     
        InputPolling()
        Update()
        Render()
        clock.tick(fps)
        counter += 1
        
        if not player.alive:
            running = False
            
        if counter > 1200:
            running = False

def MainSimulationLoop(genomes, config):
    running = True
    counter = 0
    neural_networks = []
    ais = []
    still_alive = [0]
    car_list.empty()
    
    for i, genome in genomes:
        neural_network = neat.nn.FeedForwardNetwork.create(genome, config)
        neural_networks.append(neural_network)
        genome.fitness = 0
        ai = Car(400, 180)
        ais.append(ai)
        car_list.add(ai)
    
    while running:
         
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
     
        InputSimulation(ais, neural_networks)
        UpdateSimulation(ais, genomes, still_alive)
        RenderSimulation(ais, genomes)
        clock.tick(fps)
        counter += 1
        
        if still_alive[0] == 0:
            running = False
            
        if counter > 1200:
            running = False
                           
def Quit():
    pygame.quit()

#-----------------------------------------------------SET UP--------------------------------------------------------
clock = pygame.time.Clock() # Internal Clock
screen = pygame.display.set_mode((w, h))
backdrop = pygame.image.load('res/track_1.png')
resized_background = pygame.transform.scale(backdrop, (w, h))
text_font = 0

#Player
player = Car(400, 180)

# Q-Learning variables using NEAT
config_path = 'configs/config.txt'
config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
population = neat.Population(config)
stats = neat.StatisticsReporter()

car_list = pygame.sprite.Group()

#-----------------------------------------------------MAIN LOOP-----------------------------------------------------
Init()
MainLoop()
population.run(MainSimulationLoop, 10)  
Quit()
