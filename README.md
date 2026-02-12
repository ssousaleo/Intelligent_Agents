# Refined Intelligent Agent Project by Zixuan(Lyson) Chen
## Original Project: https://github.com/danbar0/Intelligent_Agents
## Original Description:
[Smart_Bugs](https://technicallydeclined.com/a-simple-example-of-genetic-algorithms-in-python/) <--- original source

Genetic algorithm to calculate correct paths for agents to follow while avoiding obstacles

Adjust simulation parameters within the comment block labeled "Program Parameters" 

## Changes Made:
**Success Threshold:** Implemented automatic termination conditions to stop the simulation if a SUCCESS_THRESHOLD (default 97%) is met or if fitness plateaus.

**Plateau Limit:** Implemented a convergence check to automatically stop the simulation if the maximum fitness score does not improve for a set number of generations (default 40).

**Path Visualization:** Added a visited_points tracker to the Bug class to visualize the previous generation's best path as a red line on the screen.

**Reproducibility:** Added a RANDOM_SEED constant to ensure simulation runs can be exactly replicated for debugging.

**Code Standards:** Converted global configuration variables to uppercase (e.g., POPULATION, MUTATION_RATE) to adhere to standard Python styling constants.

**Generation Logic Fix:** Optimized the create_next_generation loop to correctly manage the sprite groups and mating pool weighting without the redundancy found in the old code.

**UI Enhancements:** Improved the Heads-Up Display (HUD) with semi-transparent backgrounds and added a dedicated "Results" summary screen upon completion.

**Modular Refactoring:** Extracted monolithic logic from main() into distinct helper functions like create_next_generation, setup_environment, and adjust_mutation_rate for better readability.

**Documentation:** Added comprehensive docstrings to all classes and functions (e.g., Bug, DNA, Utility) to improve code readability and maintainability.
