# MYE-041 — Project 2: R-tree & Spatial Queries

Second project for **MYE-041 Complex Data Management** (CSE, University of Ioannina).

## What the assignment asks

Build an R-tree over 2D points (restaurants in Beijing) with **STR bulk loading**, store it in a file, and then answer three kinds of spatial queries on top of it: window range queries, distance range queries, and k-nearest neighbors. The node sizes are dictated by a 1024-byte page: a leaf entry is 20 bytes (rid + x + y), so max 51 entries per leaf, and an internal entry is 36 bytes (child id + MBR), so max 28. Minimum occupancy is 40% of the max (except the root).

## How I solved it

**Building the tree (STR).** Instead of inserting points one by one, STR packs them in bulk: I sort all the points by x, cut them into vertical strips, sort each strip by y, and then chop the result into groups of 51 — each group becomes a leaf. That gives nice square-ish tiles instead of long thin ones. If the last node ends up under the 40% minimum, I "steal" a few entries from the one before it. Then I repeat the same idea one level up: the leaves become the input (sorted by the *center* of their MBR this time), get packed into internal nodes of up to 28 children, and so on until only one node is left — that's the root. Every parent stores its children's ids and MBRs, and its own MBR is the box that covers all of them.

**Storage.** The nodes live in a list where the position is the node id (it basically simulates an array on disk), and `Rtree.py` writes one line per node into `rtree.csv`: id, entry count, a leaf/internal flag, and then the entries. The query programs just parse that file back, so they don't need the build code at all.

**Queries.** All three walk the tree from the root and use the MBRs to prune: a window query only descends into children whose MBR intersects the window; a distance query only descends where the minimum distance from the query point to the MBR is within the radius; and kNN keeps the k best points in a heap and prunes any subtree whose MBR can't possibly beat the current k-th distance. The point of the whole exercise is that you touch a tiny part of the tree instead of scanning 50k points per query.

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
