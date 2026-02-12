import pygame
import pygame.gfxdraw
from pymunk import Vec2d as Vector
import random
import math
import time

pygame.init()

###############################
# Program Parameters
###############################
# -- System --
FRAMES_PER_SECOND = 240  # Speed of the simulation loop; higher is faster
DISPLAY_WIDTH = 1000  # Width of the game window in pixels
DISPLAY_HEIGHT = 1000  # Height of the game window in pixels
RANDOM_SEED = 42  # Seed for reproducible results (None = random every time)

# -- Evolution Settings --
POPULATION = 200  # Total number of bugs (agents) per generation
LIFESPAN = 100  # Duration of a generation (number of moves/frames)
MUTATION_RATE = 0.01  # 1% chance a gene (movement vector) is randomized
SUCCESS_THRESHOLD = 0.95  # Stop simulation if 95% of bugs hit the target
PLATEAU_LIMIT = 20  # Stop if max fitness score doesn't improve for 20 gens

# -- Physics / Entities --
TOTAL_OBSTACLES = 10  # Number of random black walls to generate
RESISTANCE = 1  # Velocity retention (1 = no friction, < 0.9 = high friction)
SPEED = 20  # Max force/velocity magnitude applied per frame
_SPEED_MAX = SPEED + 1  # Upper bound for random range (internal helper)
BUG_RADIUS = 20  # Radius of the bug sprite collision circle
TARGET_RADIUS = 15  # Radius of the red target circle
TARGET_Y_OFFSET = 50  # Distance of the target from the top of the screen

# -- Colors --
WHITE = (255, 255, 255)  # RGB for background
BLACK = (0, 0, 0)  # RGB for obstacles and text
RED = (220, 0, 0)  # RGB for target and alerts
GREEN = (0, 200, 0)  # RGB for standard green elements
BRIGHT_GREEN = (0, 255, 0)  # RGB for active/highlighted elements
BLUE = (0, 0, 220)  # RGB for success messages
UI_BG_COLOR = (255, 255, 255)  # Color of the semi-transparent UI panels
UI_ALPHA = 200  # Transparency level (0=invisible, 255=solid opaque)

###############################

# Set the seed immediately
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

# Calculated Global Simulation values
center_x = round(DISPLAY_WIDTH / 2)
center_y = round(DISPLAY_HEIGHT / 2)
target_location = (center_x, TARGET_Y_OFFSET)

bug_image = pygame.image.load('bug.png')  # Ensure this file exists or use a fallback rect
clock = pygame.time.Clock()
game_display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))

# Sprite data
target_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.gfxdraw.aacircle(target_surface, 15, 15, 14, RED)
pygame.gfxdraw.filled_circle(target_surface, 15, 15, 14, RED)

obstacle_list = pygame.sprite.Group()
sprite_list = pygame.sprite.Group()
sprite_target = pygame.sprite.Group()


class DNA:
    def __init__(self, genes):
        self.genes = []

        if genes:
            self.genes = genes
        else:
            for i in range(LIFESPAN):
                self.genes.append(Vector((random.randrange(-SPEED, _SPEED_MAX)),
                                         (random.randrange(-SPEED, _SPEED_MAX))))

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
        for i in range(LIFESPAN):
            if random.random() < MUTATION_RATE:
                genes[i] = Vector((random.randrange(-SPEED, _SPEED_MAX)),
                                  (random.randrange(-SPEED, _SPEED_MAX)))
        return genes


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, width, height, location_x, location_y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = location_x
        self.rect.y = location_y


class Target(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
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
        self.radius = BUG_RADIUS

        self.active_counts = 1
        self.fitness_score = 0
        self.nearest_distance = DISPLAY_HEIGHT
        self.image_center = (0, 0)
        self.count = 1
        self.wall_collision = False
        self.target_collision = False
        self.active_sprite = True
        self.birth_time = time.process_time()
        self.death_time = 0
        self.lifetime = 0

        self.visited_points = []

        self.position = Vector(center_x, DISPLAY_HEIGHT - 60)
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
            self.velocity *= RESISTANCE
            self.position += self.velocity
            self.rect = pygame.Rect(self.position.x, self.position.y, 40, 40)
            self.visited_points.append(self.rect.center)

    def update_bug_force(self):
        if self.active_sprite is True:
            if self.count < LIFESPAN:
                force_vector = DNA.get_genes(self, self.count)
                self.apply_force(force_vector)
                self.count += 1
                self.active_counts = self.count
            else:
                self.count = 1
                self.position = Vector(0, 0)
                self.position = Vector(center_x, DISPLAY_HEIGHT - 20)

            self.angle = round(-self.velocity.angle_degrees - 90)
            self.rotate_bug(self.angle)

    def rotate_bug(self, degrees):
        self.angle = degrees
        old_center = self.image.get_rect()
        rotated_image = pygame.transform.rotate(self.original_image, degrees)
        rotated_rect = old_center.copy()
        rotated_rect.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rect).copy()
        self.image = rotated_image

    def calculate_fitness(self):
        distance_from_target = math.hypot(self.position.x - target_location[0],
                                          self.position.y - target_location[1])

        if distance_from_target < self.nearest_distance:
            self.nearest_distance = distance_from_target

        if self.nearest_distance == 0 or self.target_collision is True:
            self.lifetime = self.death_time - self.birth_time
            self.fitness_score = 1 + (1 / self.lifetime) ** 2
        elif self.wall_collision is True:
            self.fitness_score = ((1 / self.nearest_distance) ** 2) * 0.1
        else:
            self.fitness_score = (1 / self.nearest_distance) ** 2

        if self.fitness_score < 0:
            self.fitness_score = 0


class Utility:
    def event_update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

    def sprite_update(self, sprite_group):
        sprite_group.draw(game_display)

    def display_update(self):
        pygame.display.flip()
        clock.tick(FRAMES_PER_SECOND)

    def quit(self):
        pygame.quit()
        exit()

    def text_objects(self, text, font):
        text_surface = font.render(text, True, BLACK)
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

    # NEW FUNCTION: Draws a semi-transparent background rect
    def draw_transparent_rect(self, x, y, width, height, color=UI_BG_COLOR, alpha=UI_ALPHA):
        s = pygame.Surface((width, height))
        s.set_alpha(alpha)
        s.fill(color)
        game_display.blit(s, (x, y))

    def reset_program(self):
        main()


def update_record(count):
    font = pygame.font.SysFont(None, 25)
    text = font.render("Fastest bug: " + str(count), True, BLACK)
    game_display.blit(text, (30, 60))


def update_status_text(count, position):
    font = pygame.font.SysFont(None, 25)
    text = font.render(str(count), True, BLACK)
    game_display.blit(text, (30, position))


def select_parents(mating_pool):
    max_index = len(mating_pool)
    if max_index > 0:
        parent_a = mating_pool[random.randrange(0, max_index)]
        parent_b = mating_pool[random.randrange(0, max_index)]
        return parent_a, parent_b
    else:
        print("index is zero!")
        return None, None


def main():
    global MUTATION_RATE  # Use the global config variable

    plateau_counter = 0
    last_generation_max_fitness = 0
    simulation_running = True
    end_reason = ""
    success_count = 0

    loop = True
    dead_bugs = 0
    update_counter = 0
    max_fitness = 0
    lifespan_counter = LIFESPAN * POPULATION
    generation_counter = 0
    progress_flag = True
    target_reached_flag = False
    progress_counter = 0

    best_path_to_draw = []

    obstacle = []
    bug = []
    mating_pool = []
    active_bugs = []
    wall = [0] * TOTAL_OBSTACLES

    u = Utility()
    target = Target()

    # Create screen bordering walls
    wall_1 = Obstacle(20, DISPLAY_HEIGHT, 0, 0)
    obstacle.append(wall_1)

    wall_2 = Obstacle(20, DISPLAY_HEIGHT, DISPLAY_WIDTH - 20, 0)
    obstacle.append(wall_2)

    wall_3 = Obstacle(DISPLAY_WIDTH, 20, 0, 0)
    obstacle.append(wall_3)

    wall_4 = Obstacle(DISPLAY_WIDTH, 20, 0, DISPLAY_HEIGHT - 20)
    obstacle.append(wall_4)

    # Create random obstacles
    for i in range(TOTAL_OBSTACLES):
        wall[i] = Obstacle(100, 20,
                           random.randrange(0, DISPLAY_HEIGHT),
                           random.randrange(110, DISPLAY_WIDTH - 150))
        obstacle.append(wall[i])

    obstacle_list.add(obstacle)
    sprite_target.add(target)
    game_display.fill(WHITE)

    # Create initial list of bug objects
    for i in range(POPULATION):
        bug.append(Bug(0))
        sprite_list.add(bug[i])
        active_bugs.append(True)

    while loop is True:
        game_display.fill(WHITE)
        u.event_update()

        # Visual result screen
        if not simulation_running:
            u.sprite_update(sprite_target)
            u.sprite_update(sprite_list)
            u.sprite_update(obstacle_list)

            if len(best_path_to_draw) > 1:
                pygame.draw.lines(game_display, RED, False, best_path_to_draw, 3)

            # --- DRAW UI BACKGROUND FOR RESULTS ---
            # Box centered on screen
            bg_w, bg_h = 400, 300
            bg_x = center_x - (bg_w // 2)
            bg_y = center_y - (bg_h // 2)
            u.draw_transparent_rect(bg_x, bg_y, bg_w, bg_h, UI_BG_COLOR, 230)

            font_title = pygame.font.SysFont("arial", 60, bold=True)
            font_sub = pygame.font.SysFont("arial", 30)

            title_surf = font_title.render("CONVERGED!", True, BLUE)
            reason_surf = font_sub.render(f"Reason: {end_reason}", True, RED)
            stats_surf = font_sub.render(f"Gen: {generation_counter} | Max Fit: {round(max_fitness, 2)}", True, BLACK)

            t_rect = title_surf.get_rect(center=(center_x, center_y - 60))
            r_rect = reason_surf.get_rect(center=(center_x, center_y))
            s_rect = stats_surf.get_rect(center=(center_x, center_y + 40))

            game_display.blit(title_surf, t_rect)
            game_display.blit(reason_surf, r_rect)
            game_display.blit(stats_surf, s_rect)

            u.draw_button("Quit", DISPLAY_WIDTH - 100, DISPLAY_HEIGHT - 100, 90, 90, RED, (230, 0, 0), u.quit)
            u.display_update()
            continue

        # Draw best path
        if len(best_path_to_draw) > 1:
            pygame.draw.lines(game_display, RED, False, best_path_to_draw, 2)

        # --- DRAW UI BACKGROUND FOR STATS ---
        # Box at top left
        u.draw_transparent_rect(10, 10, 250, 180, UI_BG_COLOR, 180)

        # Standard Status Text
        update_status_text("Generation " + str(generation_counter), 30)
        update_status_text("Mutation Rate: " + str(int(MUTATION_RATE * 100)) + " Percent", 60)
        update_status_text("Fitness Score: " + str(max_fitness), 90)
        update_status_text(f"Plateau: {plateau_counter}/{PLATEAU_LIMIT}", 120)
        update_status_text(f"Successes: {success_count}/{POPULATION}", 150)

        u.sprite_update(sprite_target)
        u.sprite_update(sprite_list)
        u.sprite_update(obstacle_list)

        update_counter += 1

        for i in range(POPULATION):
            bug[i].draw()

            if update_counter >= 10:
                for j in range(POPULATION):
                    update_counter = 0
                    lifespan_counter -= 1
                    bug[j].update_bug_force()

            bug[i].calculate_fitness()
            if bug[i].fitness_score > max_fitness:
                max_fitness = bug[i].fitness_score
                progress_flag = True

            if bug[i].active_sprite is True:
                if pygame.sprite.collide_circle(bug[i], target):
                    bug[i].death_time = time.process_time()
                    dead_bugs += 1
                    success_count += 1
                    sprite_list.remove(bug[i])
                    bug[i].active_sprite = False
                    bug[i].target_collision = True
                    target_reached_flag = True

                if pygame.sprite.spritecollide(bug[i], obstacle, False):
                    dead_bugs += 1
                    sprite_list.remove(bug[i])
                    bug[i].wall_collision = True
                    bug[i].active_sprite = False

        # End of Generation Check
        if dead_bugs >= POPULATION or lifespan_counter <= 0:
            current_best_bug = None
            current_max = -1
            for b in bug:
                if b.fitness_score > current_max:
                    current_max = b.fitness_score
                    current_best_bug = b

            if current_best_bug is not None:
                best_path_to_draw = current_best_bug.visited_points[:]

            # Convergence Check
            if (success_count / POPULATION) >= SUCCESS_THRESHOLD:
                simulation_running = False
                end_reason = f"Success Rate > {int(SUCCESS_THRESHOLD * 100)}%"
                continue

            if max_fitness > last_generation_max_fitness:
                last_generation_max_fitness = max_fitness
                plateau_counter = 0
            else:
                plateau_counter += 1

            if plateau_counter >= PLATEAU_LIMIT:
                simulation_running = False
                end_reason = f"Fitness Stalled ({PLATEAU_LIMIT} gens)"
                continue

            # Mutation adjustment logic
            if progress_flag is False:
                progress_counter += 1
                if progress_counter == 5:
                    if target_reached_flag is True and MUTATION_RATE < 0.02:
                        MUTATION_RATE += 0.01
                        progress_counter = 0
                    elif target_reached_flag is False and MUTATION_RATE < .05:
                        MUTATION_RATE += 0.02
                        progress_counter = 0
            elif progress_flag is True:
                progress_flag = False
                MUTATION_RATE = 0.01
                progress_counter = 0
                print("Successful generation!")

            print("\n")
            print("Generation " + str(generation_counter))
            print("Mutation Rate:" + "\t" * 3 + str(int(MUTATION_RATE * 100)) + " Percent")
            print("Highest Fitness Score:" + "\t" + str(max_fitness))

            for i in range(POPULATION):
                if bug[i].active_sprite is True:
                    sprite_list.remove(bug[i])
                bug[i].fitness_score /= max_fitness

            mating_pool.clear()
            for i in range(POPULATION):
                n = round(bug[i].fitness_score * 100)
                for _ in range(n):
                    mating_pool.append(bug[i])

            bug.clear()

            if len(mating_pool) == 0:
                for i in range(POPULATION):
                    bug.append(Bug(0))
            else:
                for i in range(POPULATION):
                    parent_a, parent_b = select_parents(mating_pool)
                    child = parent_a.crossover(parent_b.genes)
                    bug.append(Bug(child))

            sprite_list.add(bug)
            lifespan_counter = LIFESPAN * POPULATION
            generation_counter += 1
            dead_bugs = 0
            success_count = 0
            target_reached_flag = False

        u.draw_button("Quit", DISPLAY_WIDTH - 100, DISPLAY_HEIGHT - 100, 90, 90,
                      RED, (230, 0, 0), u.quit)
        u.display_update()


if __name__ == '__main__':
    main()
    pygame.quit()
    quit()
