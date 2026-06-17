# WGUPS Routing Program
A configurable, constraint-aware optimizer for the **Vehicle Routing Problem with Time Windows (VRP-TW)** — rebuilt from a static academic submission into a production-grade routing engine driven by a custom genetic algorithm.

---

## Overview

The VRP-TW is NP-hard: as the number of packages, trucks, and constraints grows, exact solutions become computationally intractable. This project applies a **genetic algorithm (GA)** that sidesteps the combinatorial explosion while still converging on near-optimal solutions — without the blind spots of greedy heuristics.

The core engineering challenge is that VRP-TW has two interleaved sub-problems:
1. **Assignment** — which packages go on which truck
2. **Sequencing** — in what order each truck delivers its packages

Most implementations solve these in two separate passes. This GA solves both simultaneously using a single chromosome representation, allowing assignment and sequencing decisions to co-evolve and inform each other throughout optimization.

---

## Getting Started

**Prerequisites:** [uv](https://docs.astral.sh/uv/)

```bash
git clone <repo-url>
cd c950
uv sync
```

**Run the program:**
```bash
uv run main.py
```

**Run the test suite:**
```bash
uv run pytest
```

---

## Why Rebuild?

The initial academic submission had three fundamental limitations that made it unfit for any real-world deployment:

- **No randomness tolerance.** The algorithm ran against a fixed, hand-crafted package CSV. Real logistics operations have different package counts, deadlines, and availability windows every day. The system had no mechanism to handle this variance.
- **Hard-coded loading.** Package-to-truck assignments were written directly into the source code. Any change required a developer to manually re-optimize and redeploy. There was no automated loading logic.
- **Zero scalability.** The algorithm assumed exactly 40 packages and exactly 3 trucks. It would produce incorrect results at any other scale.

The rebuild addressed all three: packages are procedurally generated with configurable constraint distributions, loading is fully automated by the GA, and truck count scales dynamically with package volume.

---

## Architecture

```
main.py
  └── run_cli()                    [cli.py]
       ├── load_csvs()             [loaders.py]  → distance matrix, address index
       └── run_ga()                [cli.py]      → user-configured GA parameters
            └── genetic_algorithm()              [genetic_algorithm.py]
                 ├── bundle_packages()           → pre-processing: reduces search space
                 ├── create_population()         → capacity-aware chromosome seeding
                 ├── [GA loop]
                 │    ├── fitness()              → multi-objective scoring
                 │    ├── tournament_selection() → k=3 pressure selection
                 │    ├── ordered_crossover()    → sentinel-aware recombination
                 │    └── mutate()               → four-strategy adaptive mutation
                 └── load_chromosome()           → assigns packages to truck objects
                      └── run_simulation()       [simulation.py]  → delivery execution
```

### Chromosome Encoding

The GA represents a complete multi-truck routing solution as a single flat array. **Negative integers act as sentinels** — boundaries between truck routes. Positive integers are bundle IDs. Order within each segment is the delivery sequence for that truck.

```
[ 2,  5,  3, -1,  7,  1, -2,  4,  6 ]
  ^--------^       ^-----^       ^---^
   Truck 1          Truck 2      Truck 3
 (bundles 2,5,3)  (bundles 7,1) (bundle 4,6)
```

This encoding lets a single crossover or mutation operator affect assignment (which truck gets a bundle) and sequencing (what order it delivers) in one operation.

### Bundle Pre-Processing

Before the GA runs, packages are grouped into **bundles** by delivery address. Each bundle is validated for constraint compatibility: a package with a `delay_time` of 9:30 AM cannot be bundled with a package that has a `deadline` of 9:00 AM. A 45-minute drive-time buffer is applied to prevent impossible groupings.

Bundling reduces the GA's search space proportionally to the number of shared-address packages, improving convergence speed without sacrificing solution quality.

---

## Genetic Algorithm — Technical Details

### Fitness Function

Every chromosome is evaluated against five weighted objectives. Lower score is better.

```python
score = (
    distance_score           +   # total fleet miles + return-to-hub
    total_minutes_late * 10  +   # gradient penalty: 5min late ≠ 5hr late
    num_late_packages  * 200 +   # per-package deadline violation
    num_capacity_over  * 2000+   # packages over truck capacity
    refrig_violations  * 2000    # refrigerated packages on wrong truck
)
```

The `minutes_late × 10` gradient penalty is significant: it creates a smooth fitness landscape where the GA can distinguish between a route that's slightly late and one that's catastrophically late. Binary pass/fail penalties flatten the landscape and stall convergence.

The fitness function also simulates the real route: departure time is set to the latest `delay_time` among a truck's bundles, and delivery times are computed at 18 mph. This means the GA is scoring actual simulated routes, not abstract proxies.

### Selection

K=3 tournament selection. Three chromosomes are sampled at random; the lowest-scoring one is selected as a parent. K=3 maintains selection pressure without eliminating population diversity the way top-N elitism alone would.

### Crossover

Sentinel-aware ordered crossover (OX):
1. Sentinel positions are locked from **parent 1** — this preserves the truck structure (how many packages each truck carries)
2. Package order is inherited from **parent 2** — this preserves delivery sequencing decisions

This operator allows the GA to explore different delivery orderings without accidentally corrupting the truck boundary structure.

### Mutation

Four strategies, applied independently per chromosome:

| Strategy | Rate | Purpose |
|---|---|---|
| Swap | `2× base_rate` | Standard package position exchange; runs most often |
| Inversion | `base_rate` | Reverses a subsequence of packages; analogous to 2-opt |
| Scramble | `adaptive` | Randomizes a 3–8 package window; scales with stagnation |
| Sentinel shift | `0.5× base_rate` | Moves a truck boundary left or right by one position |

The sentinel shift operator is specifically what prevents the population structure from fossilizing: without it, the initial capacity distribution from `create_population()` would be permanent.

### Convergence Control

- **Elitism:** Top 5 chromosomes are always copied into the next generation
- **Adaptive mutation:** If the best score doesn't improve by more than 0.1% for 50 consecutive generations, `mutation_rate` doubles to "heat" the population and escape local optima. The threshold prevents the counter from resetting on marginal gains in flat fitness landscapes. It resets to the original value once a meaningful improvement is found
- **Early termination:** If no improvement is seen for 500 generations, the GA exits and returns the current best. This enables an open-ended convergence mode: set `generations` to a very large number and let the algorithm run until it's done

---

## Performance Engineering

The GA is a hot loop — fitness is evaluated for every chromosome in every generation. Bottlenecks compound rapidly at scale. The following issues were identified and resolved across versions:

| Bottleneck | Root Cause | Resolution |
|---|---|---|
| All trucks departed at the latest possible `delay_time` | `Truck` objects maintained state across fitness evaluations — departure time from generation N carried into generation N+1 | State now initialized fresh at the start of each route evaluation in `fitness()` |
| Sentinel comparisons were expensive | Original sentinel encoding used strings (`'|1|'`), requiring `isinstance(gene, str)` on every gene in every fitness call across thousands of generations | Replaced with integer sentinels (`-1`, `-2`, ...); checking `gene < 0` is the fastest comparison available in Python — meaningful savings at GA scale |
| GA couldn't differentiate near-misses from hard failures | Binary deadline penalty treated a 1-minute miss and a 3-hour miss identically — flat fitness landscape stalls gradient-based evolution | Replaced with `minutes_late × 10` gradient penalty; fitness now reflects actual lateness severity |
| Initial populations were mostly infeasible | Pure random seeding distributed bundles without regard for truck capacity, generating chromosomes the GA spent early generations just repairing | Capacity-aware seeding: bundles are distributed evenly across truck segments in `create_population()` |
| GA wasted cycles on converged populations | No termination condition; algorithm always ran the full generation count even after convergence | Early return at 500 stagnant generations; adaptive mutation doubles at 50 to attempt escape first |

---

## Configurable Parameters

All major parameters are surfaced through the CLI. No source changes required to run different scenarios.

**Package generation:**
| Parameter | Description |
|---|---|
| Package count | Total packages to generate for the run |
| Deadline % | Fraction of packages with hard delivery deadlines |
| Delay % | Fraction of packages not available at dispatch time |
| Refrigeration % | Fraction of packages requiring refrigerated transport |

**Truck configuration:**
| Parameter | Description |
|---|---|
| Truck count | Number of trucks (default: `ceil(packages / capacity)`) |
| Capacity | Per-truck package limit |
| Refrigeration capability | Whether each truck can carry refrigerated packages |

**GA hyperparameters:**
| Parameter | Description |
|---|---|
| `pop_size` | Population size per generation |
| `generations` | Maximum generations to run (use a large value for convergence mode) |
| `mutation_rate` | Base mutation probability (adaptive logic scales from this) |

**Post-run lookup:**
After a GA run, the CLI supports package queries by ID or delivery address. Each query resolves the package's status (DELAYED / AT HUB / EN ROUTE / DELIVERED / LATE) at any user-specified timestamp — state is reconstructed from the simulation output, not re-run.

---

## Constraints Modeled

- Delivery deadlines (gradient-penalized in fitness)
- Package availability windows (`delay_time` — packages cannot be loaded before this time)
- Refrigeration requirements (truck capability matching; hard penalty)
- Per-truck capacity limits (hard penalty)
- Return-to-hub cost (distance from final delivery back to depot is included in fitness)

---

## Potential Improvements

**Heuristic Seeding:** Initialize 10% of the starting population with chromosomes built by a nearest-neighbor algorithm. Provides the GA a rational baseline from generation zero rather than spending early generations correcting random chaos.

**Dynamic Hub Reassignment:** Add a mutation operator that moves a delayed bundle between trucks. Helps when a single delayed bundle is bottlenecking a truck's departure time and no swap can resolve it.

**Physical Feasibility Audit:** Before the GA runs, flag packages where `delay_time + (distance_to_hub / speed) > deadline`. These are mathematically impossible to deliver on time — identifying them pre-run prevents the GA from wasting cycles optimizing around constraints it cannot satisfy.

**Route Visualization:** Plot delivery coordinates to visually audit routing decisions and identify geographic inefficiencies.

**PMX-Style Crossover:** The current ordered crossover always inherits sentinel positions (truck structure) from parent 1. A partially mapped crossover (PMX) variant could allow truck structure to be inherited from either parent, increasing structural diversity in the population.

**Bundle Buffer as CLI Parameter:** The 45-minute compatibility buffer used during bundle pre-processing is currently hardcoded. Surfacing it as a CLI parameter would be consistent with the project's broader parameterization philosophy and allow tuning for different fleet speeds or depot distances.
