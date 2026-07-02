# AM:4940 FOURKIOTIS ATHANASIOS
# Description: Distance Range Queries on the R-tree.
#              Loads the tree from CSV, reads the queries (qx, qy, r)
#              and finds all the points within distance r from (qx, qy).

import sys
import math


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


def min_dist_point_mbr(qx, qy, mbr): #returns the smallest possible distance from the query point to the MBR
    # Minimum distance from the point (qx,qy) to the MBR [xl,yl,xh,yh]
    # Find the closest point on the MBR and compute the distance to it

    xl = mbr[0]
    yl = mbr[1]
    xh = mbr[2]
    yh = mbr[3]

    # Closest x within [xl, xh]
    if qx < xl:
        cx = xl
    elif qx > xh:
        cx = xh
    else:
        cx = qx

    # Closest y within [yl, yh]
    if qy < yl:
        cy = yl
    elif qy > yh:
        cy = yh
    else:
        cy = qy

    dx = qx - cx
    dy = qy - cy
    return math.sqrt(dx * dx + dy * dy)  #euclidean distance


def distance_query(all_nodes, root_id, qx, qy, r):
    # DFS with a stack
    # Returns a list with all the record_ids at distance <= r from (qx, qy)

    results = []
    stack = [root_id]

    while len(stack) > 0:
        nid  = stack.pop()
        node = all_nodes[nid]

        if node["is_leaf"]:
            # Leaf: check every point
            for entry in node["entries"]:
                rid = entry[0]
                x   = entry[1][0]
                y   = entry[1][1]
                dist = math.sqrt((x - qx) * (x - qx) + (y - qy) * (y - qy))
                if dist <= r: #if the distance is within the radius, keep the record-id
                    results.append(rid)
        else:
            # Internal: check whether each child's MBR cuts the sphere of radius r
            # Paths with MINDIST(point, MBR) > r can't contain points within r
            for entry in node["entries"]:
                child_id  = entry[0]
                child_mbr = entry[1]
                if min_dist_point_mbr(qx, qy, child_mbr) <= r:
                    stack.append(child_id)

    return results


def read_queries(path):
    # Each line: "qx qy r" (center and radius)

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
        r  = float(parts[2])
        queries.append((qx, qy, r))

    return queries


def main():
    if len(sys.argv) != 4:
        print("Usage: python DistanceQuery.py <rtree.csv> <distanceQueries.txt> <output.txt>")
        sys.exit(1)

    tree_file    = sys.argv[1]
    queries_file = sys.argv[2]
    out_file     = sys.argv[3]

    all_nodes = read_tree(tree_file)

    root_id = all_nodes[-1]["node_id"]

    queries = read_queries(queries_file)

    f_out = open(out_file, "w")

    for i in range(len(queries)):
        qx, qy, r = queries[i]

        results = distance_query(all_nodes, root_id, qx, qy, r)

        results.sort()

        str_rids = []
        for rid in results:
            str_rids.append(str(rid))
        rids_str = ",".join(str_rids)

        out_line = str(i) + " (" + str(len(results)) + "): " + rids_str

        print(out_line)
        f_out.write(out_line + "\n")

    f_out.close()


main()
