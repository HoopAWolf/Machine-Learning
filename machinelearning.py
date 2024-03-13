import pygame
import neat
import math
import os
import sys
from pygame.locals import *
from matplotlib import pyplot as plt
from sklearn.tree import DecisionTreeRegressor   
from sklearn.model_selection import train_test_split
import pandas 

import csv # for csv read/write 

#-----------------------------------------------------VARIABLES-----------------------------------------------------
w, h = 960, 720 # Set dimensions of game GUI
fps   = 60  # frame rate
ani   = 4   # animation cycles
current_generation = 0 # Generation counter
BORDER_COLOR = (48, 160, 0, 255) # Set wall color
CAR_SIZE_HEIGHT = 44

IsRecording    = True # flag for if we're recording the inputs from real players
RecordedInputs = [] # list of frame data

IsRanFromData  = False # flag for if we're running the game through a external dataset 
IsRanFromAIData  = True
DataFile = 'Data/Recordings/data.csv'
InputIndex = 0

highest_score = 0
lowest_score = 0
AIDataFile = 'Data/Recordings/ai_data.csv'
AIRecordedInput = [[]] # list of list of frame data

generation_plotx = []
highestscore_ploty = []
lowestscore_ploty = []
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
            
            if self.speed > 5:
                self.speed = 5
            
    def reverse(self, amount):
        self.speed -= amount
        
        if self.speed < -3:
            self.speed = -3
        
    def check_collision(self, game_map):
        global IsRecording
        self.alive = True
        for point in self.corners:
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                if IsRecording : 
                    SaveRecordedInputsToFile(DataFile)  
                    IsRecording = False
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
        return (self.distance_travelled / (CAR_SIZE_HEIGHT * 0.5)) * 1 if self.speed > 1 else -1
        
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

class FrameData():
    def __init__(self, moves, distLeft, distHalfLeft, distFront, distHalfRight, distRight):
        self.moves = moves
        self.distLeft = distLeft
        self.distHalfLeft = distHalfLeft
        self.distFront = distFront
        self.distHalfRight = distHalfRight
        self.distRight = distRight
#-----------------------------------------------------FUNCTIONS-----------------------------------------------------
def Init(): 
    global text_font
    
    pygame.init()
    text_font = pygame.font.SysFont(None, 20)
    population.add_reporter(neat.StdOutReporter(True))

def SaveRecordedInputsToFile(data_path):
    global RecordedInputs
    with open(data_path, 'w', newline='') as datafile:
        writer = csv.writer(datafile)
        writer.writerow(['Output', 'Left', 'HalfLeft', 'Front', 'HalfRight', 'Right'])
        for frame in RecordedInputs:
            writer.writerow([frame.moves, frame.distLeft, frame.distHalfLeft, frame.distFront, frame.distHalfRight, frame.distRight])

def ReadRecordedInputsFromFile(data_path):
    global RecordedInputs
    with open(data_path, 'r') as datafile:
        reader = csv.reader(datafile)
        next(reader)
        for row in reader:
            RecordedInputs.append(FrameData(row[0], row[1], row[2], row[3], row[4], row[5]))

def InputPolling():   
    global IsRecording, RecordedInputs, WasRKeyPressed
    pressed = pygame.key.get_pressed()
    inputs = ''

    if pressed[pygame.K_DOWN]:
        player.reverse(0.05)
        inputs += '1'       
    elif pressed[pygame.K_LEFT]:
        player.turn(-1.8)
        inputs += '2'
    elif pressed[pygame.K_RIGHT]:
        player.turn(1.8)
        inputs += '3'
    else:
        player.accelerate(0.1)
        inputs += '0'

    if IsRecording and not IsRanFromData and not IsRanFromAIData:
        frame_data = player.get_distance_to_border_data()
        RecordedInputs.append(FrameData(inputs, frame_data[0], frame_data[1], frame_data[2], frame_data[3], frame_data[4]))

def RunDataInputs():
    global InputIndex, RecordedInputs
    if InputIndex >= len(RecordedInputs): 
        return
    
    inputblock = RecordedInputs[InputIndex].moves
    for input in inputblock:
        if input == '0':
            player.accelerate(0.1)
        
        if input == '1':
            player.reverse(0.05)

        if input == '2':
            player.turn(-1.8)

        if input == '3':
            player.turn(1.8)
    
    InputIndex += 1

def InputSimulation(ais, neural_networks):     
    global AIRecordedInput
    for i, ai in enumerate(ais):
        if ai.alive:            
            output = neural_networks[i].activate(ai.get_distance_to_border_data())
            choice = output.index(max(output))
            
            m = ''
            if choice == 0:
                ai.turn(-1.8) # Turn left
                m = '2'
            elif choice == 1:
                ai.turn(1.8) # Turn right
                m = '3'
            elif choice == 2:
                ai.reverse(0.05) # Slow down
                m = '1'
            else:
                ai.accelerate(0.1) # Speed up
                m = '0'
            
            frame_data = ai.get_distance_to_border_data()
            AIRecordedInput[i].append(FrameData(m, frame_data[0], frame_data[1], frame_data[2], frame_data[3], frame_data[4]))

def InputPrediction():    
    global regr
    global predicted_ai_player
    
    inputs = regr.predict([predicted_ai_player.get_distance_to_border_data()])
    # print(str(predicted_ai_player.get_distance_to_border_data()) + " Predicted Key: " + str(inputs))
    
    if int(inputs) == 1:
        predicted_ai_player.reverse(0.05)
    elif int(inputs) == 2:
        predicted_ai_player.turn(-1.8)
    elif int(inputs) == 3:
        predicted_ai_player.turn(1.8)
    else:
        predicted_ai_player.accelerate(0.1)
     
def Update():
    car_list.update(resized_background)
    
def UpdateSimulation(ais, genomes, alive_counter):
    car_list.update(resized_background)
    
    alive_counter[0] = 0
    for i, ai in enumerate(ais):
        if ai.alive:
            alive_counter[0] += 1
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
        text = text_font.render(str(int(genomes[i][1].key)) + ' ' + str(int(genomes[i][1].fitness)), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = [ai.rect.center[0], ai.rect.center[1] + 15]
        screen.blit(text, text_rect)
    
    pygame.display.update()

def MainLoop():
    global IsRanFromData, IsRanFromAIData, DataFile, RecordedInputs
    running = True
    counter = 0
    car_list.add(player)
    
    if IsRanFromData:
        ReadRecordedInputsFromFile(DataFile)
    elif IsRanFromAIData:
        ReadRecordedInputsFromFile(AIDataFile)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
     
        if not IsRanFromData and not IsRanFromAIData:
            InputPolling()
        else:
            RunDataInputs()

        Update()
        Render()
        clock.tick(fps)
        pygame.display.set_caption(str(clock.get_fps()))
        counter += 1
        
        if not player.alive:
            if IsRecording: 
                SaveRecordedInputsToFile(DataFile)
            running = False
            
        if counter > 1200:
            if IsRecording: 
                SaveRecordedInputsToFile(DataFile)    
            running = False

def MainSimulationLoop(genomes, config):
    global highest_score
    global AIRecordedInput
    global RecordedInputs
    global current_generation
    global lowest_score
    running = True
    counter = 0
    neural_networks = []
    ais = []
    alive_counter = [0]
    car_list.empty()
    AIRecordedInput.clear()
    RecordedInputs.clear()
    AIRecordedInput = [[] for i in range(0, 30)]
    
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
        UpdateSimulation(ais, genomes, alive_counter)
        RenderSimulation(ais, genomes)
        clock.tick(fps)
        pygame.display.set_caption(str(clock.get_fps()))
        counter += 1
        
        if alive_counter[0] == 0:
            running = False
            
        if counter > 1200:
            highest_index = -1
            for i, ai in enumerate(ais):
                if highest_index == -1:
                    lowest_score = highest_score = genomes[i][1].fitness
                    highest_index = i
                else:
                    if lowest_score > genomes[i][1].fitness:
                        lowest_score = genomes[i][1].fitness
                    if highest_score < genomes[i][1].fitness:
                        highest_score = genomes[i][1].fitness
                        highest_index = i
                    
            generation_plotx.append(current_generation)
            lowestscore_ploty.append(lowest_score)
            highestscore_ploty.append(highest_score)

            if highest_index > -1:  
                RecordedInputs = AIRecordedInput[highest_index]
                SaveRecordedInputsToFile(AIDataFile)  
            
            current_generation += 1
            running = False
    
            # Plot() 

def MainPredictionLoop():
    global regr
    global predicted_ai_player
    running = True
    counter = 0
    car_list.empty()
    car_list.add(predicted_ai_player)
    
    df = pandas.read_csv("Data/Recordings/all_ai_best_data.csv")
    X = df[['Left', 'HalfLeft', 'Front', 'HalfRight', 'Right']]
    y = df['Output']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 0)
    regr.fit(X_train.values, y_train)
    player = Car(400, 180)
    
    print("Decision tree:\n" )
    print("score: " + str(regr.score(X_test, y_test)))
    print("depth: " + str(regr.get_depth()))
    
    print("**************************************Predicted Player**************************************")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
     
        InputPrediction()
        Update()
        Render()
        clock.tick(fps)
        pygame.display.set_caption(str(clock.get_fps()))
        counter += 1
        
        if not predicted_ai_player.alive:
            running = False
            
        if counter > 1200:
            running = False            
                           
def Quit():
    pygame.quit()
    
def Plot():
    plt.xlabel('generation')
    plt.ylabel('highest score')
    plt.title('highest score per generation')
    plt.plot(generation_plotx, highestscore_ploty, marker = '.', label = 'highest')
    plt.plot(generation_plotx, lowestscore_ploty, marker = '.', label = 'lowest')
    
    plt.legend(['highest', 'lowest'])
    plt.grid(True)
    plt.show()

#-----------------------------------------------------SET UP--------------------------------------------------------
clock = pygame.time.Clock() # Internal Clock
screen = pygame.display.set_mode((w, h))
backdrop = pygame.image.load('res/track_1.png')
resized_background = pygame.transform.scale(backdrop, (w, h))
text_font = 0

#Player
player = Car(400, 180)
predicted_ai_player = Car(400, 180)

# Q-Learning variables using NEAT
config_path = 'configs/config.txt'
config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
population = neat.Population(config)
stats = neat.StatisticsReporter()

# Prediction model using Decision Tree Regressor
regr = DecisionTreeRegressor()

car_list = pygame.sprite.Group()

#-----------------------------------------------------MAIN LOOP-----------------------------------------------------
Init()
MainLoop()
print("Q-Learning using NEAT: Furthest distance travelled = " + str(player.distance_travelled))
MainPredictionLoop()
print("Decision Tree Regressor: Furthest distance travelled = " + str(player.distance_travelled))
# population.run(MainSimulationLoop, 50)  
Quit()
