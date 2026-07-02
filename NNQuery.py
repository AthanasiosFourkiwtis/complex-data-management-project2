# AM:4940 FOURKIOTIS ATHANASIOS
# Description: k Nearest Neighbor Queries on the R-tree.
#              Loads the tree from CSV, reads the query points (qx, qy)
#              and finds the k nearest neighbors for each query.
#              Algorithm: Incremental Best-First Search with a priority queue (heap).
#              Every point that comes off the queue is the next NN.

import sys
import math
import heapq #for the priority queue


def read_tree(path):
    # read rtree.csv and build the all_nodes list
    # indexed by node_id (position = id)

    f = open(path, "r")
    lines = f.readlines()
    f.close()

    all_nodes = []

    for line in lines:
        line = line.strip()
        if line == "":
            continue

        parts = line.split(" , ")

        node_id = int(parts[0])
        flag    = int(parts[2])
        is_leaf = (flag == 0)

        entries = []

        for i in range(3, len(parts)):
            entry_str = parts[i].strip()
            entry_str = entry_str[1:-1]

            first_comma = entry_str.index(",")
            ptr     = int(entry_str[:first_comma])
            geo_str = entry_str[first_comma + 1:].strip()

            if is_leaf:
                geo_str = geo_str[1:-1]
                coords  = geo_str.split(", ")
                x = float(coords[0])
                y = float(coords[1])
                entries.append((ptr, (x, y)))
            else:
                geo_str = geo_str[1:-1]
                coords  = geo_str.split(", ")
                xl = float(coords[0])
                yl = float(coords[1])
                xh = float(coords[2])
                yh = float(coords[3])
                entries.append((ptr, [xl, yl, xh, yh]))

        node = {
            "node_id" : node_id,
            "is_leaf" : is_leaf,
            "entries" : entries
        }
        all_nodes.append(node)

    return all_nodes


def min_dist_point_mbr(qx, qy, mbr):
    # Minimum distance from the point (qx,qy) to the MBR [xl,yl,xh,yh]
    # Lower bound: no point inside the MBR can be closer than this value

    xl = mbr[0]
    yl = mbr[1]
    xh = mbr[2]
    yh = mbr[3]

    if qx < xl:
        cx = xl
    elif qx > xh:
        cx = xh
    else:
        cx = qx

    if qy < yl:
        cy = yl
    elif qy > yh:
        cy = yh
    else:
        cy = qy

    dx = qx - cx
    dy = qy - cy
    return math.sqrt(dx * dx + dy * dy)


def knn_query(all_nodes, root_id, qx, qy, k):
    # Incremental Best-First Search with a priority queue
    # Heap elements: (distance, monot_aux, type, id)
    #   type = 0 -> node
    #   type = 1 -> point (leaf entry / record)
    # Every point that comes off the queue is the next NN
    # Stop once we have k results

    heap  = []    #priority queue
    monot = [0]   # a counter that goes up every time something enters the heap; it's needed so
    #heapq doesn't get confused when 2 elements have the same distance

    def push_node(nid, dist): #(dist, monot, 0, nid) means an internal node
        monot[0] = monot[0] + 1 # the counter goes up on every heap insert
        heapq.heappush(heap, (dist, monot[0], 0, nid))

    def push_point(rid, dist): #(dist, monot, 1, rid) means a point
        monot[0] = monot[0] + 1
        heapq.heappush(heap, (dist, monot[0], 1, rid))

    # Put in the root with distance 0.0 (always the first thing to come out)
    push_node(root_id, 0.0)

    results = []   # record-ids of the k NN, in the order they come out

    while len(heap) > 0 and len(results) < k: #keep going while there's something to explore and fewer than k points found
        d, _, typ, eid = heapq.heappop(heap) #the heap gives back the element with the smallest dist
        #eid is a node-id when typ=0 and a record-id when typ=1
        if typ == 1:
            # A point: it's the next nearest neighbor
            results.append(eid)
        else:
            # A node: explore it, pushing its children/points onto the heap
            node = all_nodes[eid] # open the node; eid is a node-id here

            if node["is_leaf"]:
                # Leaf: push all its points with their actual distance
                for entry in node["entries"]:
                    rid  = entry[0]
                    x    = entry[1][0]
                    y    = entry[1][1]
                    dist = math.sqrt((x - qx) * (x - qx) + (y - qy) * (y - qy))
                    push_point(rid, dist) #into the heap as a point
                    #it doesn't go straight into the results because some other point
                    #from another leaf might be closer. The heap decides what comes out first
            else:
                # Internal: push its children with their MINDIST
                for entry in node["entries"]:
                    child_id  = entry[0]
                    child_mbr = entry[1]
                    d_child   = min_dist_point_mbr(qx, qy, child_mbr) # MINDIST from the query point to the child's MBR
                    push_node(child_id, d_child) #into the heap as a node

    return results


def read_queries(path):
    # Each line: "qx qy" (the query point)

    f = open(path, "r")
    lines = f.readlines()
    f.close()

    queries = []
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        parts = line.split()
        qx = float(parts[0])
        qy = float(parts[1])
        queries.append((qx, qy))

    return queries


def main():
    if len(sys.argv) != 5:
        print("Usage: python NNQuery.py <rtree.csv> <NNQueries.txt> <output.txt> <k>")
        sys.exit(1)

    tree_file    = sys.argv[1]
    queries_file = sys.argv[2]
    out_file     = sys.argv[3]
    k            = int(sys.argv[4])

    all_nodes = read_tree(tree_file)

    root_id = all_nodes[-1]["node_id"]

    queries = read_queries(queries_file)

    f_out = open(out_file, "w")

    for i in range(len(queries)):
        qx, qy = queries[i]

        results = knn_query(all_nodes, root_id, qx, qy, k)

        # Output format: "i: rid1,rid2,rid3,..."  (no count, no distance)
        str_rids = []
        for rid in results:
            str_rids.append(str(rid))
        rids_str = ",".join(str_rids)

        out_line = str(i) + ": " + rids_str

        print(out_line)
        f_out.write(out_line + "\n")

    f_out.close()


main()
