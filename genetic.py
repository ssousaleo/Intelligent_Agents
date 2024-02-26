import pygame
import pygame.gfxdraw
from pymunk import Vec2d as Vector
import random
import math
import time

pygame.init()

###############################
# Program Parameters
frames_per_second = 240
total_obstacles = 1
mutation_rate = 0.01
population = 200
lifespan = 100
resistance = 1
speed = 20
###############################

# Simulation values
display_height = 1000
display_width = 1000
center_x = round(display_width / 2)
center_y = round(display_height / 2)
target_location = (center_x, 50)

bug_image = pygame.image.load('bug.png')
clock = pygame.time.Clock()
game_display = pygame.display.set_mode((display_width, display_height))

_speed = speed + 1

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (220, 0, 0)
green = (0, 200, 0)
bright_green = (0, 255, 0)
blue = (0, 0, 220)


# Sprite data
target_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.gfxdraw.aacircle(target_surface, 15, 15, 14, red)
pygame.gfxdraw.filled_circle(target_surface, 15, 15, 14, red)

obstacle_list = pygame.sprite.Group()
sprite_list = pygame.sprite.Group()
sprite_target = pygame.sprite.Group()


class DNA:
    def __init__(self, genes):
        self.genes = []

        if genes:
            self.genes = genes

        else:
            for i in range(lifespan):
                self.genes.append(Vector((random.randrange(-speed, _speed)),
                                         (random.randrange(-speed, _speed))))

    def get_genes(self, index):
        return self.genes[index]

    def crossover(self, partner_genes):
        new_genes = []
        midpoint = random.randrange(0, len(self.genes))

        for i in range(len(self.genes)):
            if i > midpoint:
                new_genes.append(self.genes[i])
            else:
                new_genes.append(partner_genes[i])

        new_genes = self.mutation(new_genes)

        return new_genes

    def mutation(self, genes):
        for i in range(lifespan):
            if random.random() < mutation_rate:
                genes[i] = Vector((random.randrange(-speed, _speed)),
                                  (random.randrange(-speed, _speed)))

        return genes

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, width, height, location_x, location_y):
        pygame.sprite.Sprite.__init__(self)

        # Dimensions of obstacle
        self.image = pygame.Surface([width, height])
        self.image.fill(black)
        self.rect = self.image.get_rect()
        self.rect.x = location_x
        self.rect.y = location_y


class Target(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        # Sprite dimension parameters
        self.image = target_surface
        self.rect = self.image.get_rect(center=target_location)
        self.radius = 10


class Bug(pygame.sprite.Sprite, DNA):
    def __init__(self, dna):
        pygame.sprite.Sprite.__init__(self)

        if dna:
            DNA.__init__(self, dna)
        else:
            DNA.__init__(self, 0)

        # Sprite dimension parameters
        self.original_image = bug_image
        self.image = bug_image
        self.rect = self.image.get_rect()
        self.radius = 20

        self.active_counts = 1
        self.fitness_score = 0
        self.nearest_distance = display_height
        self.image_center = (0, 0)
        self.count = 1
        self.wall_collision = False
        self.target_collision = False
        self.active_sprite = True
        self.birth_time = time.process_time()
        self.death_time = 0
        self.lifetime = 0

        self.position = Vector(center_x, display_height - 60)
        self.velocity = Vector(0, 0)
        self.acceleration = Vector(0, 0)

        self.angle = round(-self.velocity.angle_degrees)
        self.rotate_bug(self.angle)

    def apply_force(self, force):
        self.acceleration = force
        self.velocity = self.acceleration
        self.position += self.velocity
        self.acceleration = Vector(0, 0)

    def draw(self):
        if self.active_sprite is True:
            self.velocity *= resistance
            self.position += self.velocity
            self.rect = pygame.Rect(self.position.x, self.position.y, 40, 40)


    def update_bug_force(self):
        if self.active_sprite is True:
            if self.count < lifespan:
                force_vector = DNA.get_genes(self, self.count)
                self.apply_force(force_vector)
                self.count += 1
                self.active_counts = self.count

            else:
                self.count = 1
                self.position = Vector(0, 0)
                self.position = Vector(center_x, display_height - 20)

            self.angle = round(-self.velocity.angle_degrees - 90)
            self.rotate_bug(self.angle)

    # Rotate the bug image X degrees
    def rotate_bug(self, degrees):
        self.angle = degrees
        old_center = self.image.get_rect()
        rotated_image = pygame.transform.rotate(self.original_image, degrees)
        rotated_rect = old_center.copy()
        rotated_rect.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rect).copy()

        self.image = rotated_image

    # Calculate fitness based on time alive and distance from target
    def calculate_fitness(self):
        distance_from_target = math.hypot(self.position.x - target_location[0],
                                          self.position.y - target_location[1])

        # Set new closest distance
        if distance_from_target < self.nearest_distance:
            self.nearest_distance = distance_from_target

        # If the bug hit the target
        if self.nearest_distance == 0 or self.target_collision is True:
            self.lifetime = self.death_time - self.birth_time
            self.fitness_score = 1 + (1/self.lifetime)**2

        elif self.wall_collision is True:
            self.fitness_score = ((1 / self.nearest_distance)**2) * 0.1

        else:
            self.fitness_score = (1/self.nearest_distance)**2

        if self.fitness_score < 0:
            self.fitness_score = 0


class Utility:

    def event_update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        #self.button("Reset", center_x, center_y, 100, 50, green, bright_green, self.reset_program)

    def sprite_update(self, sprite_group):
        sprite_group.draw(game_display)

    def display_update(self):
        pygame.display.flip()
        clock.tick(frames_per_second)

    def quit(self):
        pygame.quit()

    def text_objects(self, text, font):
        text_surface = font.render(text, True, black)
        return text_surface, text_surface.get_rect()

    def draw_button(self, msg, x, y, width, height, a_color, i_color, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if x + width > mouse[0] > x and y + height > mouse[1] > y:
            pygame.draw.rect(game_display, a_color, (x, y, width, height))
            if click[0] == 1 and action is not None:
                action()

        else:
            pygame.draw.rect(game_display, i_color, (x, y, width, height))

        small_text = pygame.font.Font("freesansbold.ttf", 20)
        text_surf, text_rect = self.text_objects(msg, small_text)
        text_rect.center = ((x + (width / 2)), (y + (height / 2)))
        game_display.blit(text_surf, text_rect)

    def reset_program(self):
        #os.execv(__file__, sys.argv)
        main()



def update_record(count):
    font = pygame.font.SysFont(None, 25)
    text = font.render("Fastest bug: " + str(count), True, black)
    game_display.blit(text, (30, 60))


def update_status_text(count, position):
    font = pygame.font.SysFont(None, 25)
    text = font.render(str(count), True, black)
    game_display.blit(text, (30, position))


def select_parents(mating_pool):
    max_index = len(mating_pool)

    if max_index > 0:
        parent_a = mating_pool[random.randrange(0, max_index)]
        parent_b = mating_pool[random.randrange(0, max_index)]

        return parent_a, parent_b

    else:
        print("index is zero!")


def main():

    global mutation_rate

    loop = True
    dead_bugs = 0
    update_counter = 0
    max_fitness = 0
    lifespan_counter = lifespan * population
    generation_counter = 0
    progress_flag = True
    target_reached_flag = False
    progress_counter = 0

    obstacle = []
    bug = []
    mating_pool = []
    active_bugs = []
    wall = [0] * total_obstacles

    u = Utility()
    target = Target()

    # Create screen bordering walls
    wall_1 = Obstacle(20, display_height, 0, 0)
    obstacle.append(wall_1)

    wall_2 = Obstacle(20, display_height, display_width - 20, 0)
    obstacle.append(wall_2)

    wall_3 = Obstacle(display_width, 20, 0, 0)
    obstacle.append(wall_3)

    wall_4 = Obstacle(display_width, 20, 0, display_height - 20)
    obstacle.append(wall_4)

    # Create random obstacles
    for i in range(total_obstacles):
        wall[i] = Obstacle(100, 20, random.randrange(0, display_height), random.randrange(110, display_width - 150))
        obstacle.append(wall[i])

    obstacle_list.add(obstacle)
    sprite_target.add(target)
    game_display.fill(white)

    # Create initial list of bug objects
    for i in range(population):
        bug.append(Bug(0))
        sprite_list.add(bug[i])
        active_bugs.append(True)


    #player.play_wave(synthesizer.generate_chord(chord, 10.0))

    while loop is True:
        game_display.fill(white)
        u.event_update()
        update_status_text("Generation " + str(generation_counter), 30)
        update_status_text("Mutation Rate: " + str(int(mutation_rate * 100)) + " Percent", 60)
        update_status_text("Fitness Score: " + str(max_fitness), 90)
        u.sprite_update(sprite_target)
        u.sprite_update(sprite_list)
        u.sprite_update(obstacle_list)

        # Update bug variables
        update_counter += 1

        for i in range(population):

            bug[i].draw()

            if update_counter >= 10:
                for j in range(population):
                    update_counter = 0
                    lifespan_counter -= 1
                    bug[j].update_bug_force()

            # Calculate bug's fitness
            bug[i].calculate_fitness()
            if bug[i].fitness_score > max_fitness:
                max_fitness = bug[i].fitness_score
                progress_flag = True

            if bug[i].active_sprite is True:
                if pygame.sprite.collide_circle(bug[i], target):
                    bug[i].death_time = time.process_time()
                    dead_bugs += 1
                    sprite_list.remove(bug[i])
                    bug[i].active_sprite = False
                    bug[i].target_collision = True
                    target_reached_flag = True

                if pygame.sprite.spritecollide(bug[i], obstacle,  False):
                    dead_bugs += 1
                    sprite_list.remove(bug[i])
                    bug[i].wall_collision = True
                    bug[i].active_sprite = False

        # End generation if all bugs are DEAD
        if dead_bugs >= population:
            lifespan_counter = 0

            if progress_flag is False:
                progress_counter += 1

                if progress_counter == 5:
                    if target_reached_flag is True and mutation_rate < 0.02:
                        mutation_rate += 0.01
                        progress_counter = 0

                    elif target_reached_flag is False and mutation_rate < .05:
                        mutation_rate += 0.02
                        progress_counter = 0

            elif progress_flag is True:
                progress_flag = False
                mutation_rate = 0.01
                progress_counter = 0

                print("Sucessful generation!")

            print("\n")
            print("Generation " + str(generation_counter))
            print("Mutation Rate:" + "\t"*3 + str(int(mutation_rate * 100)) + " Percent")
            print("Highest Fitness Score:" + "\t" + str(max_fitness))

        # Calculate fitness scores and create new population
        if lifespan_counter == 0:

            for i in range(population):
                if bug[i].active_sprite is True:
                    sprite_list.remove(bug[i])

                bug[i].fitness_score /= max_fitness

            # Determine mating pool
            mating_pool.clear()
            for i in range(population):
                n = round(bug[i].fitness_score * 100)

                j = 0
                while j <= n:
                    mating_pool.append(bug[i])
                    j += 1

            # Create children
            bug.clear()
            for i in range(population):
                parent_a, parent_b = select_parents(mating_pool)
                child = parent_a.crossover(parent_b.genes)

                bug.append(Bug(child))
                sprite_list.add(bug)

            lifespan_counter = lifespan * population
            generation_counter += 1
            dead_bugs = 0

        u.draw_button("Quit", display_width - 100, display_height - 100, 90, 90,
                       (255, 0, 0), (230, 0, 0), quit)
        u.display_update()


if __name__ == '__main__':
    main()
    pygame.quit()
    quit()
