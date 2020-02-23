"""Hier wird mit der Maus, Linien gezeichnet um einen Rennstrecke für das 2D Auto zu erstellen"""
import pickle
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
GREY = (100, 100, 100)

WALL_POINTS_LIST = []
FITNESS_POINTS_LIST = []


def text_on_screen():
    """Writes all the Text on Screen"""
    text = STAT_FONT.render("Wall(W) and close line(F), Startpoint(S), Fitnessline(L)", True, BLACK)
    height_of_text = 0
    SCREEN.blit(text, (0, height_of_text))


def main():
    """main function"""
    mode = "WALL"
    wall_nr = 0

    running = True
    SCREEN.fill(GREY)
    while running:
        CLOCK.tick(FPS)
        text_on_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    mode = "WALL"
                elif event.key == pygame.K_s:
                    mode = "START"
                elif event.key == pygame.K_l:
                    mode = "FITNESS"

            if mode == "WALL":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        WALL_POINTS_LIST.append(WALL_POINTS_LIST[0])
                        pygame.draw.line(SCREEN, WHITE, WALL_POINTS_LIST[-2], WALL_POINTS_LIST[-1])
                        if wall_nr == 0:
                            pickle.dump(WALL_POINTS_LIST, open("Rennstrecke_Aussen.txt", "wb"))
                            wall_nr = 1
                        else:
                            pickle.dump(WALL_POINTS_LIST, open("Rennstrecke_Innen.txt", "wb"))
                            wall_nr = 0
                        WALL_POINTS_LIST.clear()

                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse_position = pygame.mouse.get_pos()
                    WALL_POINTS_LIST.append(mouse_position)

            if mode == "START":
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_position = pygame.mouse.get_pos()
                    pickle.dump(mouse_position, open("Startpunkt.txt", "wb"))
                    pygame.draw.circle(SCREEN, WHITE, mouse_position, 5)

            if mode == "FITNESS":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        if len(FITNESS_POINTS_LIST) % 2 != 0:
                            del FITNESS_POINTS_LIST[-1]
                        pickle.dump(FITNESS_POINTS_LIST, open("Fitnesslinien.txt", "wb"))
                        FITNESS_POINTS_LIST.clear()
                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse_position = pygame.mouse.get_pos()
                    FITNESS_POINTS_LIST.append(mouse_position)

        if len(WALL_POINTS_LIST) > 2:
            pygame.draw.lines(SCREEN, WHITE, False, WALL_POINTS_LIST)

        if len(FITNESS_POINTS_LIST) > 1 and len(FITNESS_POINTS_LIST) % 2 == 0:
            for i in range(0, len(FITNESS_POINTS_LIST), 2):
                pygame.draw.line(SCREEN, WHITE, FITNESS_POINTS_LIST[i], FITNESS_POINTS_LIST[i+1])

        pygame.display.update()


if __name__ == '__main__':
    main()
