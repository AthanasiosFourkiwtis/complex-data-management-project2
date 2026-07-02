# MYE-041 — Project 2: R-tree & Spatial Queries

Second assignment for **MYE-041 Complex Data Management**, Department of Computer Science & Engineering, University of Ioannina.

## Contents

- `Rtree.py` — R-tree construction with STR bulk loading
- `WindowQuery.py` — Window range queries
- `NNQuery.py` — k-nearest neighbor queries
- `DistanceQuery.py` — Distance range queries
- `Beijing_restaurants.txt` — Input data (coordinates of restaurants in Beijing)
- `windowRangeQueries.txt`, `distanceRangeQueries.txt`, `NNQueries.txt` — Query files
- `rtree.csv`, `out_*.txt` — Sample output files
- `Anafora2.pdf` — Project report
- `Assignment2.pdf` — Assignment handout

## Usage

### Step 1 — Build the R-tree

Takes the points file and produces `rtree.csv` (the serialized R-tree). **Must be run first**, since all the queries rely on `rtree.csv`:

```bash
python Rtree.py <input_points> <output_csv>
# example:
python Rtree.py Beijing_restaurants.txt rtree.csv
```

On completion it prints tree statistics (height, nodes per level, average MBR area).

### Step 2 — Window Range Queries

Returns every point that falls inside each rectangular query window:

```bash
python WindowQuery.py <rtree_csv> <queries_file> <output_file>
# example:
python WindowQuery.py rtree.csv windowRangeQueries.txt out_win.txt
```

### Step 3 — Distance Range Queries

Returns every point within a given distance of each query point:

```bash
python DistanceQuery.py <rtree_csv> <queries_file> <output_file>
# example:
python DistanceQuery.py rtree.csv distanceRangeQueries.txt out_dist.txt
```

### Step 4 — k-NN Queries

Returns the `k` nearest points to each query point. Takes `k` as an extra argument:

```bash
python NNQuery.py <rtree_csv> <queries_file> <output_file> <k>
# example (k=5):
python NNQuery.py rtree.csv NNQueries.txt out_nn.txt 5
```

## Author

Athanasios Fourkiotis (student ID 4940)
