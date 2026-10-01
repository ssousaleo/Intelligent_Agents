# Genetic Algorithm: Evolving Bugs to Reach a Target

This genetic algorithm **evolves movement sequences that guide bugs from the bottom of the screen to a red target near the top while avoiding black obstacles**. It is a visual demonstration of optimization: successful movement sequences are more likely to be inherited by the next generation.

## Genetic Algorithm Concepts

| Concept | What it represents in this code |
|---|---|
| Individual | One bug attempting to reach the target |
| Population | 200 bugs per generation |
| Chromosome/DNA | A sequence of 100 movement vectors |
| Gene | One vector `(x, y)`, with each component between −5 and 5 |
| Fitness | A score based on proximity to the target, collisions, and reaching time |
| Selection | Higher-scoring bugs have a greater chance of becoming parents |
| Crossover | Combine portions of two parents’ movement sequences |
| Mutation | Randomly replace some movement vectors |

## 1. Start with Random Movement Sequences

Each bug starts near the bottom with randomly generated DNA. For example:

```python
[(2, -4), (-1, -5), (3, 0), ...]
```

Negative `y` values move upward; positive `y` values move downward. The bugs execute these instructions; **they do not observe obstacles and decide how to react**. The algorithm searches for a useful sequence through repeated trials.

## 2. Evaluate How Well Each Bug Performs

For a bug that has not reached the target, the fitness is:

$$
\text{fitness}=\frac{1}{d_{\min}^{2}}
$$

Here, $d_{\min}$ is the closest distance it has achieved to the target. Getting closer gives a higher score—even if the bug later moves away.

If it hits a wall, its score receives a penalty:

$$
\text{fitness}=\frac{0.1}{d_{\min}^{2}}
$$

If it reaches the target, it receives:

$$
\text{fitness}=1+\frac{1}{t^{2}}
$$

Here, $t$ is its measured lifetime. This strongly favors reaching the target, with an additional reward for reaching it sooner.

## 3. Select Parents

The code divides each score by the highest fitness recorded so far, then uses the normalized score to determine how many copies of that bug enter a mating pool.

| Normalized fitness | Copies in the pool |
|---:|---:|
| 1.00 | 100 |
| 0.50 | 50 |
| 0.10 | 10 |
| 0.00 | 0 |

Parents are randomly drawn from this pool. Better bugs therefore have more chances to reproduce. Very low scores can round to zero and disappear from the pool.

## 4. Combine and Mutate Their DNA

For each child, the algorithm chooses a random crossover point. For example, with the crossover point at index 2:

| Sequence | Gene 0 | Gene 1 | Gene 2 | Gene 3 | Gene 4 | Gene 5 |
|---|---|---|---|---|---|---|
| Parent A | A0 | A1 | A2 | A3 | A4 | A5 |
| Parent B | B0 | B1 | B2 | B3 | B4 | B5 |
| Child | B0 | B1 | B2 | A3 | A4 | A5 |

It then randomly replaces genes with new movement vectors. Initially, each gene has a **1% mutation probability**, so a 100-gene child has one mutation on average.

When progress stalls, the code attempts to increase mutation to encourage exploration. When fitness improves, it restores the starting rate.

## 5. Repeat Until a Stopping Condition Is Met

Each new generation starts again from the bottom. The simulation stops when either:

- **At least 97% of bugs reach the target**—194 of the 200 bugs.
- The best recorded fitness fails to improve for **40 generations**.

The red line shows the **best path recorded across generations**. The best bug’s DNA is not automatically preserved; there is no explicit elitism.

## Implementation Details for Classroom Use

- **It optimizes reaching the target and measured speed, not explicitly the shortest path.**
- The speed reward uses `time.process_time()`—CPU time—so the random seed alone does not guarantee identical evolution across runs.
- Movement occurs in both `apply_force()` and `draw()`, and new genes are applied roughly every ten display frames. Thus, “100 genes” does not mean 100 animation frames.
- Gene index `0` is skipped because the movement counter starts at `1`.
- The results screen says “CONVERGED!” even when it stops because of a plateau. That can happen without finding a successful route.
- Running it requires `pygame`, `pymunk`, and a separate `bug.png` image.

## Main Teaching Idea

**Each bug is a candidate solution; executing its DNA evaluates that solution; selection, crossover, and mutation produce the next set of candidates.**
