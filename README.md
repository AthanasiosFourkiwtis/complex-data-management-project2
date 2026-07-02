# MYE-041 — Project 2: R-tree & Spatial Queries

Second project for **MYE-041 Complex Data Management** (CSE, University of Ioannina).

## What's in here

- `Rtree.py` — builds the R-tree with STR bulk loading
- `WindowQuery.py` — window range queries
- `NNQuery.py` — k-nearest neighbor queries
- `DistanceQuery.py` — distance range queries
- `Beijing_restaurants.txt` — input data (restaurant coordinates in Beijing)
- `windowRangeQueries.txt`, `distanceRangeQueries.txt`, `NNQueries.txt` — the query files
- `rtree.csv`, `out_*.txt` — example output files
- `Anafora2.pdf` — my report
- `Assignment2.pdf` — the assignment description

## How to run

### Step 1 — Build the R-tree

Takes the points file and produces `rtree.csv` (the serialized R-tree). This has to run first, since all the queries read `rtree.csv`:

```bash
python Rtree.py <input_points> <output_csv>
# example:
python Rtree.py Beijing_restaurants.txt rtree.csv
```

At the end it prints some stats (height, nodes per level, average MBR area).

### Step 2 — Window Range Queries

Returns all the points inside each rectangular window:

```bash
python WindowQuery.py <rtree_csv> <queries_file> <output_file>
# example:
python WindowQuery.py rtree.csv windowRangeQueries.txt out_win.txt
```

### Step 3 — Distance Range Queries

Returns all the points within a given distance from each query point:

```bash
python DistanceQuery.py <rtree_csv> <queries_file> <output_file>
# example:
python DistanceQuery.py rtree.csv distanceRangeQueries.txt out_dist.txt
```

### Step 4 — k-NN Queries

Returns the `k` closest points for each query point. Takes one extra argument, `k`:

```bash
python NNQuery.py <rtree_csv> <queries_file> <output_file> <k>
# example (k=5):
python NNQuery.py rtree.csv NNQueries.txt out_nn.txt 5
```

## Author

Athanasios Fourkiotis (student ID 4940)
