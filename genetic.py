# Refined Intelligent Agent Project by Zixuan(Lyson) Chen
# Original Project: https://github.com/danbar0/Intelligent_Agents
#
# Changes Made:
# Success Threshold: Implemented automatic termination conditions to stop the simulation if a SUCCESS_THRESHOLD (default 97%) is met or if fitness plateaus.
# Plateau Limit: Implemented a convergence check to automatically stop the simulation if the maximum fitness score does not improve for a set number of generations (default 40).
# Path Visualization: Added a visited_points tracker to the Bug class to visualize the previous generation's best path as a red line on the screen.
# Reproducibility: Added a RANDOM_SEED constant to ensure simulation runs can be exactly replicated for debugging.
# Code Standards: Converted global configuration variables to uppercase (e.g., POPULATION, MUTATION_RATE) to adhere to standard Python styling constants.
# Generation Logic Fix: Optimized the create_next_generation loop to correctly manage the sprite groups and mating pool weighting without the redundancy found in the old code.
# UI Enhancements: Improved the Heads-Up Display (HUD) with semi-transparent backgrounds and added a dedicated "Results" summary screen upon completion.
# Modular Refactoring: Extracted monolithic logic from main() into distinct helper functions like create_next_generation, setup_environment, and adjust_mutation_rate for better readability.
# Documentation: Added comprehensive docstrings to all classes and functions (e.g., Bug, DNA, Utility) to improve code readability and maintainability.


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
SUCCESS_THRESHOLD = 0.97  # Stop simulation if designated % of bugs hit the target
PLATEAU_LIMIT = 40  # Stop if max fitness score doesn't improve for the designated gens

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
    """
    Handles genetic data (movement vectors) for the agents.
    """

    def __init__(self, genes):
        """
        Initialize DNA with specific genes or random vectors.

        Args:
            genes (list or int): List of vectors if inheritance, else 0/None for random.
        """
        self.genes = []

        if genes:
            self.genes = genes
        else:
            for i in range(LIFESPAN):
                self.genes.append(Vector((random.randrange(-SPEED, _SPEED_MAX)),
                                         (random.randrange(-SPEED, _SPEED_MAX))))

    def get_genes(self, index):
        """Returns the vector at the specified gene index."""
        return self.genes[index]

    def crossover(self, partner_genes):
        """
        Mixes genes with a partner's genes to create a new DNA sequence.

        Args:
            partner_genes (list): The gene list of the partner agent.

        Returns:
            list: The new hybrid gene list after mutation.
        """
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
        """
        Randomly alters genes based on the global mutation rate.

        Args:
            genes (list): The gene list to mutate.

        Returns:
            list: The mutated gene list.
        """
        for i in range(LIFESPAN):
            if random.random() < MUTATION_RATE:
                genes[i] = Vector((random.randrange(-SPEED, _SPEED_MAX)),
                                  (random.randrange(-SPEED, _SPEED_MAX)))
        return genes


class Obstacle(pygame.sprite.Sprite):
    """
    Represents a static wall or obstacle in the simulation.
    """

    def __init__(self, width, height, location_x, location_y):
        """
        Initialize a black rectangular obstacle.

        Args:
            width (int): Width of the obstacle.
            height (int): Height of the obstacle.
            location_x (int): X coordinate.
            location_y (int): Y coordinate.
        """
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = location_x
        self.rect.y = location_y


class Target(pygame.sprite.Sprite):
    """
    Represents the goal (red circle) agents try to reach.
    """

    def __init__(self):
        """Initialize the target sprite."""
        pygame.sprite.Sprite.__init__(self)
        self.image = target_surface
        self.rect = self.image.get_rect(center=target_location)
        self.radius = 10


class Bug(pygame.sprite.Sprite, DNA):
    """
    Represents an agent in the population that moves and evolves.
    """

    def __init__(self, dna):
        """
        Initialize a bug with specific or random DNA.

        Args:
            dna (list or int): The genetic code for this bug.
        """
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
        """
        Applies a vector force to the bug's acceleration.

        Args:
            force (Vector): The force vector to apply.
        """
        self.acceleration = force
        self.velocity = self.acceleration
        self.position += self.velocity
        self.acceleration = Vector(0, 0)

    def draw(self):
        """Updates the bug's visual position and records its path."""
        if self.active_sprite is True:
            self.velocity *= RESISTANCE
            self.position += self.velocity
            self.rect = pygame.Rect(self.position.x, self.position.y, 40, 40)
            self.visited_points.append(self.rect.center)

    def update_bug_force(self):
        """Retrieves the next movement vector from DNA and applies it."""
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
        """
        Rotates the bug sprite image.

        Args:
            degrees (float): The angle to rotate to.
        """
        self.angle = degrees
        old_center = self.image.get_rect()
        rotated_image = pygame.transform.rotate(self.original_image, degrees)
        rotated_rect = old_center.copy()
        rotated_rect.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rect).copy()
        self.image = rotated_image

    def calculate_fitness(self):
        """Calculates the fitness score based on distance to target, collision, and speed."""
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
    """
    Helper class for Pygame events, drawing, and UI updates.
    """

    def event_update(self):
        """Processes pygame events, handling Quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

    def sprite_update(self, sprite_group):
        """Draws a sprite group to the display."""
        sprite_group.draw(game_display)

    def display_update(self):
        """Updates the full display and ticks the clock."""
        pygame.display.flip()
        clock.tick(FRAMES_PER_SECOND)

    def quit(self):
        """Exits the application."""
        pygame.quit()
        exit()

    def text_objects(self, text, font):
        """Creates a text surface and rect for rendering."""
        text_surface = font.render(text, True, BLACK)
        return text_surface, text_surface.get_rect()

    def draw_button(self, msg, x, y, width, height, a_color, i_color, action=None):
        """
        Draws an interactive button.

        Args:
            msg (str): Button text.
            x, y, width, height (int): Dimensions and position.
            a_color (tuple): Active color (hover).
            i_color (tuple): Inactive color.
            action (func): Callback function when clicked.
        """
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
        """
        Draws a rectangle with alpha transparency.

        Args:
            x, y, width, height (int): Dimensions and position.
            color (tuple): RGB color.
            alpha (int): Transparency 0-255.
        """
        s = pygame.Surface((width, height))
        s.set_alpha(alpha)
        s.fill(color)
        game_display.blit(s, (x, y))

    def reset_program(self):
        """Resets the simulation by calling main()."""
        main()


def update_record(count):
    """Draws record text to screen (Legacy helper)."""
    font = pygame.font.SysFont(None, 25)
    text = font.render("Fastest bug: " + str(count), True, BLACK)
    game_display.blit(text, (30, 60))


def update_status_text(text_content, position):
    """
    Draws specific status text at a vertical Y position.

    Args:
        text_content (str): The string to display.
        position (int): The y-coordinate.
    """
    font = pygame.font.SysFont(None, 25)
    text = font.render(text_content, True, BLACK)
    game_display.blit(text, (30, position))


def select_parents(mating_pool):
    """
    Selects two random parents from the weighted mating pool.

    Args:
        mating_pool (list): List of Bug objects weighted by fitness.

    Returns:
        tuple: (parent_a, parent_b)
    """
    max_index = len(mating_pool)
    if max_index > 0:
        parent_a = mating_pool[random.randrange(0, max_index)]
        parent_b = mating_pool[random.randrange(0, max_index)]
        return parent_a, parent_b
    else:
        print("index is zero!")
        return None, None


def setup_environment():
    """
    Initializes and places all static obstacles (walls) in the environment.
    """
    obstacle = []

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
        rand_wall = Obstacle(100, 20,
                             random.randrange(0, DISPLAY_HEIGHT),
                             random.randrange(110, DISPLAY_WIDTH - 150))
        obstacle.append(rand_wall)

    obstacle_list.add(obstacle)


def create_initial_population():
    """
    Creates the first generation of bugs with random DNA.

    Returns:
        list: A list of Bug objects.
    """
    bugs = []
    for i in range(POPULATION):
        bugs.append(Bug(0))
        sprite_list.add(bugs[i])
    return bugs


def draw_results_screen(u, end_reason, generation_counter, max_fitness, best_path_to_draw):
    """
    Renders the final summary screen when simulation ends.

    Args:
        u (Utility): Utility instance.
        end_reason (str): Why the simulation stopped.
        generation_counter (int): Final generation count.
        max_fitness (float): Highest fitness achieved.
        best_path_to_draw (list): Points of the best path.
    """
    u.sprite_update(sprite_target)
    u.sprite_update(sprite_list)
    u.sprite_update(obstacle_list)

    if len(best_path_to_draw) > 1:
        pygame.draw.lines(game_display, RED, False, best_path_to_draw, 3)

    # Draw UI background for results
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


def draw_hud(u, generation_counter, max_fitness, plateau_counter, success_count, best_path_to_draw):
    """
    Draws the heads-up display with statistics during the simulation.

    Args:
        u (Utility): Utility instance.
        generation_counter (int): Current generation.
        max_fitness (float): Current max fitness.
        plateau_counter (int): Current stall counter.
        success_count (int): Number of bugs reaching target.
        best_path_to_draw (list): Points of the best path from previous gen.
    """
    # Draw best path
    if len(best_path_to_draw) > 1:
        pygame.draw.lines(game_display, RED, False, best_path_to_draw, 2)

    # Draw UI background for stats
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


def adjust_mutation_rate(progress_flag, target_reached_flag, progress_counter, starting_rate):
    """
    Adjusts the global mutation rate dynamically based on progress.

    Args:
        progress_flag (bool): Whether fitness improved this gen.
        target_reached_flag (bool): Whether any bug hit the target.
        progress_counter (int): Counter for stagnant generations.
        starting_rate (float): The baseline mutation rate.

    Returns:
        tuple: (new_progress_flag, new_progress_counter)
    """
    global MUTATION_RATE

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
        MUTATION_RATE = starting_rate
        progress_counter = 0
        print("Successful generation!")

    return progress_flag, progress_counter


def create_next_generation(bugs, max_fitness):
    """
    Generates the next population using selection, crossover, and mutation.

    Args:
        bugs (list): The current generation of bugs.
        max_fitness (float): The max fitness score used for normalization.

    Returns:
        list: The new list of Bug objects.
    """
    # Normalize fitness scores
    for i in range(POPULATION):
        if bugs[i].active_sprite is True:
            sprite_list.remove(bugs[i])
        bugs[i].fitness_score /= max_fitness

    # Create mating pool
    mating_pool = []
    for i in range(POPULATION):
        n = round(bugs[i].fitness_score * 100)
        for _ in range(n):
            mating_pool.append(bugs[i])

    bugs.clear()
    new_bugs = []

    # Crossover
    if len(mating_pool) == 0:
        for i in range(POPULATION):
            new_bugs.append(Bug(0))
    else:
        for i in range(POPULATION):
            parent_a, parent_b = select_parents(mating_pool)
            child = parent_a.crossover(parent_b.genes)
            new_bugs.append(Bug(child))

    sprite_list.add(new_bugs)
    return new_bugs


def main():
    """
    The main simulation loop controlling the genetic algorithm.
    """
    global MUTATION_RATE  # Use the global config variable

    # Initialize State
    starting_mutation_rate = MUTATION_RATE
    plateau_counter = 0
    last_generation_max_fitness = 0
    simulation_running = True
    end_reason = ""
    success_count = 0

    dead_bugs = 0
    update_counter = 0
    max_fitness = 0
    lifespan_counter = LIFESPAN * POPULATION
    generation_counter = 0
    progress_flag = True
    target_reached_flag = False
    progress_counter = 0

    best_path_to_draw = []
    global_best_fitness = 0

    # Setup Logic
    u = Utility()
    target = Target()
    sprite_target.add(target)

    setup_environment()
    bug = create_initial_population()
    active_bugs = [True] * POPULATION  # Kept for consistency with original logic structure

    loop = True
    while loop is True:
        game_display.fill(WHITE)
        u.event_update()

        # Visual result screen (Simulation Ended)
        if not simulation_running:
            draw_results_screen(u, end_reason, generation_counter, max_fitness, best_path_to_draw)
            u.display_update()
            continue

        # Draw HUD and active simulation elements
        draw_hud(u, generation_counter, max_fitness, plateau_counter, success_count, best_path_to_draw)

        # Physics & Logic Update Loop
        update_counter += 1

        for i in range(POPULATION):
            bug[i].draw()

            if update_counter >= 10:
                for j in range(POPULATION):
                    # Note: Logic preserved from original - update_counter reset inside loop
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

                if pygame.sprite.spritecollide(bug[i], obstacle_list, False):
                    dead_bugs += 1
                    sprite_list.remove(bug[i])
                    bug[i].wall_collision = True
                    bug[i].active_sprite = False

        # End of Generation Check
        if dead_bugs >= POPULATION or lifespan_counter <= 0:

            # Find the single best bug of this generation
            current_gen_best_bug = None
            current_gen_max = -1

            for b in bug:
                if b.fitness_score > current_gen_max:
                    current_gen_max = b.fitness_score
                    current_gen_best_bug = b

            # Update Global Best Path
            if current_gen_best_bug is not None:
                if current_gen_max > global_best_fitness:
                    global_best_fitness = current_gen_max
                    best_path_to_draw = current_gen_best_bug.visited_points[:]

            # Check: Convergence (Success Rate)
            if (success_count / POPULATION) >= SUCCESS_THRESHOLD:
                simulation_running = False
                end_reason = f"Success Rate > {int(SUCCESS_THRESHOLD * 100)}%"
                continue

            # Check: Convergence (Plateau)
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
            progress_flag, progress_counter = adjust_mutation_rate(
                progress_flag, target_reached_flag, progress_counter, starting_mutation_rate
            )

            # Print Stats
            print("\n")
            print("Generation " + str(generation_counter))
            print("Mutation Rate:" + "\t" * 3 + str(int(MUTATION_RATE * 100)) + " Percent")
            print("Highest Fitness Score:" + "\t" + str(max_fitness))

            # Create Next Generation
            bug = create_next_generation(bug, max_fitness)

            # Reset Counters
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
