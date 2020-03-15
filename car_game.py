"""Ein 2D Auto lernt mit NEAT wie man eine Rennstrecke fährt"""
import pickle
import math
import os
import neat
from shapely.geometry import LineString
import pygame

pygame.init()

WIN_WIDTH = 1280
WIN_HEIGHT = 1024

SCREEN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
CLOCK = pygame.time.Clock()
FPS = 60 #Frames per second.

#How long in seconds a Car survives after the last fitness line
DEATH_AFTER_SECONDS = 5

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GREY = (100, 100, 100)

FONT = pygame.font.Font(None, 30)

OUTER_WALL_POINTS_LIST = pickle.load(open("Rennstrecke_Aussen.txt", "rb"))
INNER_WALL_POINTS_LIST = pickle.load(open("Rennstrecke_Innen.txt", "rb"))
FITNESS_POINTS_LIST = pickle.load(open("Fitnesslinien.txt", "rb"))
START_POINT = pickle.load(open("Startpunkt.txt", "rb"))

with open('best_car_genom.txt', 'rb') as f:
    BEST_CAR = pickle.load(f)

class Car:
    """Car"""
    def __init__(self):
        self.half_width = 10
        self.half_height = 20
        self.detection_range = 8
        self.center_pos = pygame.Vector2(START_POINT[0], START_POINT[1])
        self.corner_top_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y - self.half_height)
        self.corner_top_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y - self.half_height)
        self.corner_bottom_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y + self.half_height)
        self.corner_bottom_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y + self.half_height)
        self.corner_list = [self.corner_top_left, self.corner_top_right, self.corner_bottom_right, self.corner_bottom_left]
        self.corner_rotated = self.corner_list[:]

        self.top_left_detection_point = pygame.Vector2(self.center_pos.x - self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.top_right_detection_point = pygame.Vector2(self.center_pos.x + self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.top_detection_point = pygame.Vector2(self.center_pos.x, self.center_pos.y - self.half_height * self.detection_range)
        self.detection_point_list = [self.top_left_detection_point, self.top_right_detection_point, self.top_detection_point]
        self.detection_point_rotated = self.detection_point_list[:]

        self.top_left_distance_point = self.top_left_detection_point
        self.top_right_distance_point = self.top_right_detection_point
        self.top_distance_point = self.top_detection_point
        self.distance_point_list = [self.top_left_distance_point, self.top_right_distance_point, self.top_distance_point]

        self.top_left_found = False
        self.top_right_found = False
        self.top_found = False

        self.distance_list = [math.sqrt(math.pow(self.half_width * self.detection_range, 2) + math.pow(self.half_height * self.detection_range, 2)), math.sqrt(math.pow(self.half_width * self.detection_range, 2) + math.pow(self.half_height * self.detection_range, 2)), self.detection_range * self.half_height]

        self.velocity = pygame.Vector2(0, 0)
        self.color = GREEN
        self.acceleration = 25
        self.drag = 0.9
        self.angle = 0
        self.radian = 0
        self.angular_velocity = 0
        self.angular_drag = 0.2
        self.turn_speed = 4
        self.next_fitness = 0
        self.fitness = 0
        self.seconds_since_last_fitness = 0

    def rotate_points(self, point_list):
        """rot"""
        for i, vector in enumerate(point_list):
            tempX = vector.x - self.center_pos.x
            tempY = vector.y - self.center_pos.y

            rotatedX = tempX*math.cos(self.radian) - tempY*math.sin(self.radian)
            rotatedY = tempX*math.sin(self.radian) + tempY*math.cos(self.radian)

            x = int(rotatedX + self.center_pos.x)
            y = int(rotatedY + self.center_pos.y)
            temp = pygame.Vector2(x, y)
            point_list[i] = temp
        return point_list

    def draw(self):
        """Zeichnet das Auto"""
        pygame.draw.lines(SCREEN, self.color, True, self.corner_rotated)
        if self.collision_with_wall():
            self.color = RED
        else:
            self.color = GREEN
        pygame.draw.circle(SCREEN, self.color, (int(self.center_pos.x), int(self.center_pos.y)), 5)
        for point in self.detection_point_list:
            pygame.draw.line(SCREEN, self.color, point, self.center_pos)
        for distance in self.distance_point_list:
            pygame.draw.circle(SCREEN, self.color, (int(distance[0]), int(distance[1])), 5)
        pygame.draw.lines(SCREEN, self.color, True, self.corner_list)

    def move(self, delta_time):
        """Wie das Auto sich bewegt, jeden Frame"""
        self.center_pos += self.velocity * delta_time
        self.velocity *= self.drag
        self.angle += self.angular_velocity * delta_time
        self.angular_velocity *= self.angular_drag
        self.radian = self.angle * math.pi / 180
        self.corner_top_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y - self.half_height)
        self.corner_top_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y - self.half_height)
        self.corner_bottom_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y + self.half_height)
        self.corner_bottom_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y + self.half_height)
        self.corner_list = [self.corner_top_left, self.corner_top_right, self.corner_bottom_right, self.corner_bottom_left]

        self.top_left_detection_point = pygame.Vector2(self.center_pos.x - self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.top_right_detection_point = pygame.Vector2(self.center_pos.x + self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.top_detection_point = pygame.Vector2(self.center_pos.x, self.center_pos.y - self.half_height * self.detection_range)
        self.detection_point_list = [self.top_left_detection_point, self.top_right_detection_point, self.top_detection_point]

        self.calculate_distance_points()
        self.distance_point_list = [self.top_left_distance_point, self.top_right_distance_point, self.top_distance_point]

        for i in range(0, len(self.distance_list)):
            self.distance_list[i] = math.sqrt(pow(abs(self.distance_point_list[i][0] - self.center_pos.x), 2) + pow(abs(self.distance_point_list[i][1] - self.center_pos.y), 2))

        self.seconds_since_last_fitness += delta_time
        self.corner_rotated = self.rotate_points(self.corner_list)
        self.detection_point_rotated = self.rotate_points(self.detection_point_list)

    def accelerate(self):
        """Beschleunigung des Autos"""
        self.velocity.x += math.sin(self.radian) * self.acceleration
        self.velocity.y -= math.cos(self.radian) * self.acceleration

    def rotate_right(self):
        """Nach Recht lenken"""
        self.angular_velocity += self.turn_speed
        self.angle += self.turn_speed

    def rotate_left(self):
        """Nach Links lenken"""
        self.angular_velocity -= self.turn_speed
        self.angle -= self.turn_speed

    def collision_with_wall(self):
        """Gibt True zurück falls das Auto die Wand berührt"""
        for i in range(0, len(OUTER_WALL_POINTS_LIST)-1):
            # top
            if line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[1]):
                return True
            # left
            if line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[3]):
                return True
            # right
            elif line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[1], self.corner_rotated[2]):
                return True
            # bottom
            # elif line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[2], self.corner_rotated[3]):
            #     return True

        for i in range(0, len(INNER_WALL_POINTS_LIST)-1):
            # top
            if line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[1]):
                return True
            # left
            if line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[3]):
                return True
            # right
            elif line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[1], self.corner_rotated[2]):
                return True
            # bottom
            # elif line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[2], self.corner_rotated[3]):
            #     return True
            
        return False

    def collision_with_fitness_line(self):
        """Prüft ob das Auto die Fitness Linie berührt"""
        if line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[0], self.corner_rotated[1]):
            self.next_fitness += 2
            if self.next_fitness == len(FITNESS_POINTS_LIST):
                self.next_fitness = 0
            return True
        elif line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[0], self.corner_rotated[3]):
            self.next_fitness += 2
            if self.next_fitness == len(FITNESS_POINTS_LIST):
                self.next_fitness = 0
            return True
        elif line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[1], self.corner_rotated[2]):
            self.next_fitness += 2
            if self.next_fitness == len(FITNESS_POINTS_LIST):
                self.next_fitness = 0
            return True
        #bottom
        # elif line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[2], self.corner_rotated[3]):
        #     self.next_fitness += 2
        #     if self.next_fitness == len(FITNESS_POINTS_LIST):
        #         self.next_fitness = 0
        #     return True
        return False

    def calculate_distance_points(self):
        self.top_left_distance_point = self.detection_point_rotated[0]
        self.top_right_distance_point = self.detection_point_rotated[1]
        self.top_distance_point = self.detection_point_rotated[2]

        self.top_left_found = False
        self.top_right_found = False
        self.top_found = False


        for i in range(0, len(OUTER_WALL_POINTS_LIST)-1):
            if not self.top_left_found:
                if line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.center_pos, self.detection_point_rotated[0]):
                    self.top_left_distance_point = line_intersection_point((OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1]), (self.center_pos, self.detection_point_rotated[0]))
                    self.top_left_found = True

            if not self.top_right_found:
                if line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.center_pos, self.detection_point_rotated[1]):
                    self.top_right_distance_point = line_intersection_point((OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1]), (self.center_pos, self.detection_point_rotated[1]))
                    self.top_right_found = True

            if not self.top_found:
                if line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.center_pos, self.detection_point_rotated[2]):
                    self.top_distance_point = line_intersection_point((OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1]), (self.center_pos, self.detection_point_rotated[2]))
                    self.top_found = True
        

    
        for i in range(0, len(INNER_WALL_POINTS_LIST)-1):
            if not self.top_left_found:
                if line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.center_pos, self.detection_point_rotated[0]):
                    self.top_left_distance_point = line_intersection_point((INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1]), (self.center_pos, self.detection_point_rotated[0]))
                    self.top_left_found = True

            if not self.top_right_found:
                if line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.center_pos, self.detection_point_rotated[1]):
                    self.top_right_distance_point = line_intersection_point((INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1]), (self.center_pos, self.detection_point_rotated[1]))
                    self.top_right_found = True

            if not self.top_found:
                if line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.center_pos, self.detection_point_rotated[2]):
                    self.top_distance_point = line_intersection_point((INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1]), (self.center_pos, self.detection_point_rotated[2]))
                    self.top_found = True




def line_intersect(p1, p2, p3, p4):
    line = LineString([p1, p2])
    other = LineString([p3, p4])
    if line.intersects(other):
        return True
    else:
        return False


def line_intersection_point(line1, line2):
    """Nimmt (A, B), (C, D) als Argument, diese sind 4 Punkte und gibt zurück ob sich die Linien die durch diese Punkte entstanden sind sich kreuzen oder nicht"""
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        """determinante berechnen"""
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def draw_on_screen(car):
    """Zeichnet die Rennstrecke, ohne Fitnesslinien und Startpunkt"""
    pygame.draw.lines(SCREEN, WHITE, False, OUTER_WALL_POINTS_LIST)
    pygame.draw.lines(SCREEN, WHITE, False, INNER_WALL_POINTS_LIST)
    car.draw()

    #Zeichnet Fitnesslinie und Startpunkt
    #pygame.draw.line(SCREEN, WHITE, FITNESS_POINTS_LIST[car.next_fitness], FITNESS_POINTS_LIST[car.next_fitness+1])
    #pygame.draw.circle(SCREEN, WHITE, START_POINT, 5)

def move_draw(car, delta_time):
    car.move(delta_time)
    draw_on_screen(car)

#random genom wird genommen und viele Autos werden erzeugt:
def main(genomes, config):
    """main function"""
    cars = []
    genom = []
    nets = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        cars.append(Car())
        g.fitness = 0
        genom.append(g)

    running = True
    while running:
        delta_time = CLOCK.tick(FPS) / 1000
        SCREEN.fill(GREY)

        current_fps = FONT.render(str(int(CLOCK.get_fps())), True, WHITE)
        SCREEN.blit(current_fps, (50, 50))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()


        for x, car in enumerate(cars):
            if car.collision_with_wall() or car.seconds_since_last_fitness > DEATH_AFTER_SECONDS:
                genom[x].fitness -= 10
                cars.pop(x)
                nets.pop(x)
                genom.pop(x)

            elif car.collision_with_fitness_line():
                genom[x].fitness += 10
                car.seconds_since_last_fitness = 0
                car.fitness += 10

            if car.fitness >= 6000:
                running = False

            move_draw(car, delta_time)

        if not cars:
            running = False
            break

        for x, car in enumerate(cars):
            output = nets[x].activate((car.distance_list[0], car.distance_list[1], car.distance_list[2]))
            if output[0] > 0.5:
                car.accelerate()
            if output[1] > 0.5:
                car.rotate_right()
            if output[2] > 0.5:
                car.rotate_left()


        pygame.display.update()

#winner genom wird genommen und nur der gewinner wird laufen:
def main_one(genomes, config):
    """main function"""
    car = Car()
    genom = 0
    net = neat.nn.FeedForwardNetwork.create(BEST_CAR, config)
    for _, g in genomes:
        g.fitness = 0
        genom = g

    
    running = True
    while running:
        delta_time = CLOCK.tick(FPS) / 1000
        SCREEN.fill(GREY)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()


        if car.collision_with_wall() or car.seconds_since_last_fitness > DEATH_AFTER_SECONDS:
            genom.fitness -= 5
            running = False
            break

        if car.collision_with_fitness_line():
            genom.fitness += 10
            car.seconds_since_last_fitness = 0
            car.fitness += 10


        if car.fitness >= 6000:
            running = False
            break

        move_draw(car, delta_time)

        output = net.activate((car.distance_list[0], car.distance_list[1], car.distance_list[2]))
        if output[0] > 0.5:
            car.accelerate()
        if output[1] > 0.2:
            car.rotate_right()
        if output[2] > 0.2:
            car.rotate_left()


        pygame.display.update()


def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_file)
    p = neat.Population(config)
    p.add_reporter((neat.StdOutReporter(True)))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 5000)
    print(winner)
    # pickle.dump(winner, open("best_car_genom.txt", "wb"))
    # with open("asd.txt", "w") as fi:
    #     fi.write(str(winner))


def change_feedforward(population):
    feedforward_string = F"""
    [NEAT]
    fitness_criterion     = max
    fitness_threshold     = 6000
    pop_size              = {population}
    reset_on_extinction   = False

    [DefaultGenome]
    # node activation options
    activation_default      = tanh
    activation_mutate_rate  = 0.0
    activation_options      = tanh sigmoid

    # node aggregation options
    aggregation_default     = sum
    aggregation_mutate_rate = 0.0
    aggregation_options     = sum

    # node bias options
    bias_init_mean          = 0.0
    bias_init_stdev         = 1.0
    bias_max_value          = 30.0
    bias_min_value          = -30.0
    bias_mutate_power       = 0.5
    bias_mutate_rate        = 0.7
    bias_replace_rate       = 0.1

    # genome compatibility options
    compatibility_disjoint_coefficient = 1.0
    compatibility_weight_coefficient   = 0.5

    # connection add/remove rates
    conn_add_prob           = 0.5
    conn_delete_prob        = 0.5

    # connection enable options
    enabled_default         = True
    enabled_mutate_rate     = 0.01

    feed_forward            = True
    initial_connection      = full

    # node add/remove rates
    node_add_prob           = 0.2
    node_delete_prob        = 0.2

    # network parameters
    num_hidden              = 0
    num_inputs              = 3
    num_outputs             = 3

    # node response options
    response_init_mean      = 1.0
    response_init_stdev     = 0.0
    response_max_value      = 30.0
    response_min_value      = -30.0
    response_mutate_power   = 0.0
    response_mutate_rate    = 0.0
    response_replace_rate   = 0.0

    # connection weight options
    weight_init_mean        = 0.0
    weight_init_stdev       = 1.0
    weight_max_value        = 30
    weight_min_value        = -30
    weight_mutate_power     = 0.5
    weight_mutate_rate      = 0.8
    weight_replace_rate     = 0.1

    [DefaultSpeciesSet]
    compatibility_threshold = 3.0

    [DefaultStagnation]
    species_fitness_func = max
    max_stagnation       = 1
    species_elitism      = 4

    [DefaultReproduction]
    elitism            = 4
    survival_threshold = 0.2"""

    with open("config-feedforward.txt", "w") as feed:
        feed.write(feedforward_string)



if __name__ == '__main__':
    # change_feedforward(10)
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
