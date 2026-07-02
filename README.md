# Complex Data Management, Project 2: R-tree & Spatial Queries

Second project for the Complex Data Management course (CSE, University of Ioannina).

## What the assignment asks

Build an R-tree over 2D points, restaurants in Beijing, using STR bulk loading, store it in a file, and then answer three kinds of spatial queries on top of it: window range queries, distance range queries and k-nearest neighbors. The node sizes come from a 1024 byte page. A leaf entry is 20 bytes (rid plus x plus y) so a leaf fits at most 51 entries, and an internal entry is 36 bytes (child id plus MBR) so at most 28. Minimum occupancy is 40% of the max, except for the root.

## How I solved it

Instead of inserting points one by one, STR packs them in bulk. I sort all the points by x, cut them into vertical strips, sort each strip by y, and then chop the result into groups of 51, and each group becomes a leaf. That gives nice square-ish tiles instead of long thin ones. If the last node ends up under the 40% minimum, it steals a few entries from the one before it. Then the same idea repeats one level up: the leaves become the input, sorted by the center of their MBR this time, and get packed into internal nodes of up to 28 children, and so on until only one node is left, which is the root. Every parent stores its children's ids and MBRs, and its own MBR is the box covering all of them.

The nodes live in a list where the position is the node id, which basically simulates an array on disk, and `Rtree.py` writes one line per node into `rtree.csv` with the id, the entry count, a leaf or internal flag and then the entries. The query programs just parse that file back, so they never need the build code.

All three queries walk the tree from the root and prune with the MBRs. The window query only descends into children whose MBR intersects the window. The distance query only descends where the minimum distance from the query point to the MBR is within the radius. The kNN query runs an incremental best-first search with a heap, pushing internal nodes with their MINDIST and points with their real distance, and every point that pops out of the heap is the next nearest neighbor. The whole point of the exercise is that a query touches a tiny part of the tree instead of scanning 50 thousand points.

## What's in here

`Rtree.py` builds the tree, and `WindowQuery.py`, `DistanceQuery.py` and `NNQuery.py` answer the three query types. The input is `Beijing_restaurants.txt`, the query workloads are in `windowRangeQueries.txt`, `distanceRangeQueries.txt` and `NNQueries.txt`, and `rtree.csv` with the `out_*.txt` files are example outputs. My report is `Anafora2.pdf` and the assignment description is `Assignment2.pdf`.

## How to run

First build the tree. This has to run before anything else, since all the queries read `rtree.csv`. At the end it prints some stats about the height, the nodes per level and the average MBR area.

```bash
python Rtree.py Beijing_restaurants.txt rtree.csv
```

Then the queries. Window and distance take the tree, the query file and an output file, and the kNN one takes an extra argument for k:

```bash
python WindowQuery.py rtree.csv windowRangeQueries.txt out_win.txt
python DistanceQuery.py rtree.csv distanceRangeQueries.txt out_dist.txt
python NNQuery.py rtree.csv NNQueries.txt out_nn.txt 5
```

## Author

Athanasios Fourkiotis (student ID 4940)
