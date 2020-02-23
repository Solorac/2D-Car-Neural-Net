"""Hier wird mit der Maus, Linien gezeichnet um einen Rennstrecke für das 2D Auto zu erstellen"""
import pickle
import math
from shapely.geometry import LineString
import pygame
pygame.font.init()

WIN_WIDTH = 1280
WIN_HEIGHT = 1024

STAT_FONT = pygame.font.SysFont("arial", 40)
SCREEN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
CLOCK = pygame.time.Clock()
FPS = 60 #Frames per second.

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GREY = (100, 100, 100)

OUTER_WALL_POINTS_LIST = pickle.load(open("Rennstrecke_Aussen.txt", "rb"))
INNER_WALL_POINTS_LIST = pickle.load(open("Rennstrecke_Innen.txt", "rb"))
FITNESS_POINTS_LIST = pickle.load(open("Fitnesslinien.txt", "rb"))
START_POINT = pickle.load(open("Startpunkt.txt", "rb"))

class Car:
    """Car"""
    def __init__(self):
        self.half_width = 10
        self.half_height = 20
        self.detection_range = 4
        self.center_pos = pygame.Vector2(START_POINT[0], START_POINT[1])
        self.corner_top_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y - self.half_height)
        self.corner_top_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y - self.half_height)
        self.corner_bottom_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y + self.half_height)
        self.corner_bottom_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y + self.half_height)
        self.corner_list = [self.corner_top_left, self.corner_top_right, self.corner_bottom_right, self.corner_bottom_left]
        self.corner_rotated = self.corner_list[:]

        self.top_left_detection_point = pygame.Vector2(self.center_pos.x - self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.top_right_detection_point = pygame.Vector2(self.center_pos.x + self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.bottom_left_detection_point = pygame.Vector2(self.center_pos.x - self.half_width * self.detection_range, self.center_pos.y + self.half_height * self.detection_range)
        self.bottom_right_detection_point = pygame.Vector2(self.center_pos.x + self.half_width * self.detection_range, self.center_pos.y + self.half_height * self.detection_range)
        self.top_detection_point = pygame.Vector2(self.center_pos.x, self.center_pos.y - self.half_height * self.detection_range)
        self.detection_point_list = [self.top_left_detection_point, self.top_right_detection_point, self.bottom_left_detection_point, self.bottom_right_detection_point, self.top_detection_point]
        self.detection_point_rotated = self.detection_point_list[:]

        self.velocity = pygame.Vector2(0, 0)
        self.color = GREEN
        self.acceleration = 0.5
        self.drag = 0.9
        self.angle = 0
        self.radian = 0
        self.angular_velocity = 0
        self.angular_drag = 0.9
        self.turn_speed = 0.4
        self.fitness = 0
        self.next_fitness = 0

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
        """Zeichnet Rechteck vom Auto"""
        self.corner_rotated = self.rotate_points(self.corner_list)
        self.detection_point_rotated = self.rotate_points(self.detection_point_list)

        if self.collision_with_wall():
            self.color = RED
        else:
            self.color = GREEN
        #pygame.draw.circle(SCREEN, self.color, (int(self.center_pos.x), int(self.center_pos.y)), 5)
        pygame.draw.lines(SCREEN, self.color, True, self.corner_rotated)
        for point in self.detection_point_list:
            pygame.draw.line(SCREEN, self.color, point, self.center_pos)
        #pygame.draw.lines(SCREEN, self.color, True, self.corner_list)



    def move(self):
        """Wie das Auto sich bewegt, jeden Frame"""
        self.center_pos += self.velocity
        self.velocity *= self.drag
        self.angle += self.angular_velocity
        self.angular_velocity *= self.angular_drag
        self.radian = self.angle * math.pi / 180
        self.corner_top_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y - self.half_height)
        self.corner_top_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y - self.half_height)
        self.corner_bottom_left = pygame.Vector2(self.center_pos.x - self.half_width, self.center_pos.y + self.half_height)
        self.corner_bottom_right = pygame.Vector2(self.center_pos.x + self.half_width, self.center_pos.y + self.half_height)
        self.corner_list = [self.corner_top_left, self.corner_top_right, self.corner_bottom_right, self.corner_bottom_left]
        self.collision_with_fitness_line()

        self.top_left_detection_point = pygame.Vector2(self.center_pos.x - self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.top_right_detection_point = pygame.Vector2(self.center_pos.x + self.half_width * self.detection_range, self.center_pos.y - self.half_height * self.detection_range)
        self.bottom_left_detection_point = pygame.Vector2(self.center_pos.x - self.half_width * self.detection_range, self.center_pos.y + self.half_height * self.detection_range)
        self.bottom_right_detection_point = pygame.Vector2(self.center_pos.x + self.half_width * self.detection_range, self.center_pos.y + self.half_height * self.detection_range)
        self.top_detection_point = pygame.Vector2(self.center_pos.x, self.center_pos.y - self.half_height * self.detection_range)
        self.detection_point_list = [self.top_left_detection_point, self.top_right_detection_point, self.bottom_left_detection_point, self.bottom_right_detection_point, self.top_detection_point]

    def accelerate(self):
        """Beschleunigung des Autos"""
        self.velocity.x += math.sin(self.radian) * self.acceleration
        self.velocity.y -= math.cos(self.radian) * self.acceleration

    def decelerate(self):
        """Bremsen und Rückwärtsgang des Autos"""
        self.velocity.x -= math.sin(self.radian) * self.acceleration
        self.velocity.y += math.cos(self.radian) * self.acceleration

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
            if line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[1]):
                return True
            elif line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[3]):
                return True
            elif line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[2], self.corner_rotated[3]):
                return True
            elif line_intersect(OUTER_WALL_POINTS_LIST[i], OUTER_WALL_POINTS_LIST[i+1], self.corner_rotated[1], self.corner_rotated[2]):
                return True

        for i in range(0, len(INNER_WALL_POINTS_LIST)-1):
            if line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[1]):
                return True
            elif line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[0], self.corner_rotated[3]):
                return True
            elif line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[2], self.corner_rotated[3]):
                return True
            elif line_intersect(INNER_WALL_POINTS_LIST[i], INNER_WALL_POINTS_LIST[i+1], self.corner_rotated[1], self.corner_rotated[2]):
                return True

    def collision_with_fitness_line(self):
        """Prüft ob das Auto die Fitness Linie berührt"""
        if line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[0], self.corner_rotated[1]):
            self.next_fitness += 2
            if(self.next_fitness == len(FITNESS_POINTS_LIST)):
                self.next_fitness = 0
        elif line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[0], self.corner_rotated[3]):
            self.next_fitness += 2
            if(self.next_fitness == len(FITNESS_POINTS_LIST)):
                self.next_fitness = 0
        elif line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[2], self.corner_rotated[3]):
            self.next_fitness += 2
            if(self.next_fitness == len(FITNESS_POINTS_LIST)):
                self.next_fitness = 0
        elif line_intersect(FITNESS_POINTS_LIST[self.next_fitness], FITNESS_POINTS_LIST[self.next_fitness+1], self.corner_rotated[1], self.corner_rotated[2]):
            self.next_fitness += 2
            if(self.next_fitness == len(FITNESS_POINTS_LIST)):
                self.next_fitness = 0


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
    if div == 0:
        return 0

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
    pygame.draw.line(SCREEN, WHITE, FITNESS_POINTS_LIST[car.next_fitness], FITNESS_POINTS_LIST[car.next_fitness+1])
    #pygame.draw.circle(SCREEN, WHITE, START_POINT, 5)

def main():
    """main function"""


    caro = Car()
    running = True
    while running:
        CLOCK.tick(FPS)
        SCREEN.fill(GREY)

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_w]:
            caro.accelerate()
        if pressed[pygame.K_s]:
            caro.decelerate()
        if pressed[pygame.K_a]:
            caro.rotate_left()
        if pressed[pygame.K_d]:
            caro.rotate_right()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()

        caro.move()
        draw_on_screen(caro)
        pygame.display.update()

if __name__ == '__main__':
    main()
