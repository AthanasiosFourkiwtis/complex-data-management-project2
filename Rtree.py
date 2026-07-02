# AM:4940 FOURKIOTIS ATHANASIOS
# Description: Reads points from a file, builds an in-memory R-tree with STR
#              bulk loading, writes it out to CSV, and prints statistics.

import sys
import math

# CONSTANTS
# Each node = 1024 bytes
# Leaf     : rid(4B) + x(8B) + y(8B) = 20B -> MAX = floor(1024/20) = 51
# Internal : nid(4B) + 4*8B (MBR) = 36B    -> MAX = floor(1024/36) = 28
# MIN = 40% of MAX (R-tree rule, so nodes never end up nearly empty)

MAX_LEAF = 51
MAX_INT  = 28
MIN_LEAF = 20   # floor(0.4 * 51) = 20
MIN_INT  = 11   # floor(0.4 * 28) = 11


def mbr_of_points(point_list):
    # takes a list of (x,y) and returns the [x_low, y_low, x_high, y_high]
    x_low  = point_list[0][0]
    x_high = point_list[0][0]
    y_low  = point_list[0][1]
    y_high = point_list[0][1]

    for s in point_list:
        if s[0] < x_low:
            x_low = s[0]
        if s[0] > x_high:
            x_high = s[0]
        if s[1] < y_low:
            y_low = s[1]
        if s[1] > y_high:
            y_high = s[1]

    return [x_low, y_low, x_high, y_high]


def mbr_of_mbrs(mbr_list):
    # same idea, but the input is a list of MBRs (not points)
    # needed when building a parent, whose MBR must enclose all its children's MBRs
    x_low  = mbr_list[0][0]
    y_low  = mbr_list[0][1]
    x_high = mbr_list[0][2]
    y_high = mbr_list[0][3]

    for m in mbr_list:
        if m[0] < x_low:
            x_low = m[0]
        if m[1] < y_low:
            y_low = m[1]
        if m[2] > x_high:
            x_high = m[2]
        if m[3] > y_high:
            y_high = m[3]

    return [x_low, y_low, x_high, y_high]


def mbr_area(mbr):
    return (mbr[2] - mbr[0]) * (mbr[3] - mbr[1]) #width = x_high - x_low
                                                 #height = y_high - y_low
                                                 #area = width * height


def read_points(path): #reads Beijing_restaurants.txt
    # first line = point count (ignored; we just read whatever we find)
    # every other line: "x y"
    f = open(path, "r")
    lines = f.readlines()
    f.close()

    points = [] #empty list for the points
    for i in range(1, len(lines)): #start at 1, not 0, since line 0 holds the count (51970)
        g = lines[i].strip() #drop the trailing \n
        if g == "":   #skip blank lines
            continue
        parts = g.split() # e.g. "39.856 116.423"->.split()->["39.856", "116.423"]->float()->(39.856, 116.423)-> x=39.856 and y=116.423
        x = float(parts[0]) #parts[0], parts[1] are strings and you can't do math on strings, so convert to float
        y = float(parts[1])
        points.append((x, y)) # double parentheses because we append one tuple, not 2 arguments — append takes a single argument

    return points

def split_into_groups(lst, size): # used to cut the points into leaves of 51, or nodes into groups of 28
    # breaks the list into sublists of 'size' elements
    # the last group may hold fewer
    # e.g. [1,2,3,4,5], size=2  ->  [[1,2], [3,4], [5]]
    groups = []
    current_group = []
    for item in lst:
        current_group.append(item)
        if len(current_group) == size:
            groups.append(current_group)
            current_group = []

    # keep the last group even if it's smaller than 'size'
    if len(current_group) > 0:
        groups.append(current_group)

    return groups


def fix_underflow(groups, minimum):
    # if the last node holds fewer entries than the minimum,
    # we "steal" elements from the second-to-last one
    # exception: a single group = the root, nothing to do

    if len(groups) < 2:
        return groups # with only 1 group (i.e. the root) do nothing, since the root is exempt from the minimum

    last = groups[-1]

    if len(last) >= minimum:
        return groups   # all good

    # how many elements are missing
    missing = minimum - len(last)
    second_to_last = groups[-2]

    # take the last 'missing' elements of the second-to-last group
    extras = second_to_last[-missing:]
    groups[-2] = second_to_last[:-missing] # replace the second-to-last group with everything except its last 'missing' elements
    groups[-1] = extras + last # replace the last group with the moved extras + whatever it already held.
      # it's extras + last and not last + extras because the elements are sorted by y (from STR). The orphan point
      # has the largest y in the dataset. The extras (tail of the second-to-last group) have a smaller y than the orphan but a larger y than what remained in the second-to-last group.

   # print("underflow fix: last group now holds", len(groups[-1]))  # debug
    return groups

def point_key_x(entry):
    # entry = (record_id, (x, y)) -> returns x for sorting
    return entry[1][0]


def point_key_y(entry):
    # returns y for sorting
    return entry[1][1]
 # the 2 helpers above tell sorted() which coordinate to sort by

def str_pack_leaves(entries): #takes entries and returns the groups that will become leaves
    # entries = list of (record_id, (x,y))
    # returns a list of groups -> each group becomes one leaf

    N = len(entries) # if there are no points, return an empty list
    if N == 0:
        return []

    # how many leaves are needed
    P = math.ceil(N / MAX_LEAF)
    # how many vertical slices -> we want roughly square spatial "tiles"
    S = math.ceil(math.sqrt(P))
    if S < 1:
        S = 1

    # print("leaves: N =", N, " P =", P, " S =", S)  # debug

    # Step 1: sort by x (left to right on the map)
    sortd_x = sorted(entries, key=point_key_x)

    # Step 2: cut into S vertical slices (each slice = S*MAX_LEAF elements)
    slices = split_into_groups(sortd_x, S * MAX_LEAF)

    # Step 3: within each slice, sort by y and append to the final list
    final = []
    for slc in slices:
        sortd_y = sorted(slc, key=point_key_y)
        for eg in sortd_y:
            final.append(eg)

    # Step 4: cut into groups of MAX_LEAF + fix underflow
    groups = split_into_groups(final, MAX_LEAF)
    groups = fix_underflow(groups, MIN_LEAF)

    return groups

def node_key_x(node):
    # returns the center_x of the node's MBR (for sorting)
    mbr = node["mbr"]
    return (mbr[0] + mbr[2]) / 2.0


def node_key_y(node):
    # returns the center_y of the node's MBR (for sorting)
    mbr = node["mbr"]
    return (mbr[1] + mbr[3]) / 2.0

def str_pack_nodes(node_list):
    # same idea as str_pack_leaves, but for child nodes
    # sorted by MBR CENTER (not corner)

    N = len(node_list)
    if N == 0:
        return []

    P = math.ceil(N / MAX_INT)
    S = math.ceil(math.sqrt(P))
    if S < 1:
        S = 1

    # Step 1: sort by the MBR's center_x
    sortd_x = sorted(node_list, key=node_key_x)

    # Step 2: cut into vertical slices
    slices = split_into_groups(sortd_x, S * MAX_INT)

    # Step 3: within each slice, sort by center_y
    final = []
    for slc in slices:
        sortd_y = sorted(slc, key=node_key_y)
        for k in sortd_y:
            final.append(k)

    # Step 4: cut into groups of MAX_INT + fix underflow
    groups = split_into_groups(final, MAX_INT)
    groups = fix_underflow(groups, MIN_INT)

    return groups

def build_tree(points): # builds the leaves with STR, then repeatedly builds parents. Each parent stores its children's node-ids and MBRs, and the process stops once a single node — the root — remains.
    # record_id = line number in the file, starting at 1
    entries = []
    for i in range(len(points)): # assign a record-id to every point
        rid = i + 1
        entries.append((rid, points[i]))

    # nodes go into a list — their position is their node_id
    # simulates an on-disk array
    all_nodes = []
    levels = []        # for the statistics

    # ===== LEVEL 0: leaves (STR) =====
    leaf_groups = str_pack_leaves(entries)
    level_0 = []

    for group in leaf_groups:
        node_id = len(all_nodes)   # the node's position in the list

        # the leaf's MBR, computed from its points
        group_points = []
        for eg in group:
            group_points.append(eg[1])
        mbr = mbr_of_points(group_points)

        leaf = {
            "node_id" : node_id,
            "is_leaf" : True,
            "entries" : group,    # list of (rid, (x,y))
            "mbr"     : mbr
        }
        all_nodes.append(leaf)
        level_0.append(leaf)

    levels.append(level_0)
    # print("Level 0:", len(level_0), "leaves")  # debug

    # ===== LEVELS 1, 2, ... up to the root (bulk loading, no re-sorting) =====
    current = level_0

    while len(current) > 1: #as long as more than 1 node remains, parents must be built
        node_groups = str_pack_nodes(current)
        #instead of the line above we could have used the two lines below
       # node_groups = split_into_groups(current, MAX_INT)
       #node_groups = fix_underflow(node_groups, MIN_INT)
        next_level = []

        for group in node_groups: # build one parent for every group of children
            node_id = len(all_nodes) #assign a node-id to the new node

            entries = [] # what the internal node will store
            child_mbrs = [] # for computing the parent's MBR
            for child in group:
                entries.append((child["node_id"], child["mbr"])) # for each child, store its node-id and MBR
                child_mbrs.append(child["mbr"])

            mbr = mbr_of_mbrs(child_mbrs)

            node = {
                "node_id" : node_id,
                "is_leaf" : False,
                "entries" : entries,   # list of (child_id, child_mbr)
                "mbr"     : mbr
            }
            all_nodes.append(node)
            next_level.append(node)

        levels.append(next_level)
        # print("New level:", len(next_level), "nodes")  # debug
        current = next_level

    return all_nodes, levels

def write_csv(all_nodes, path): #writes the R-tree to a file, one line per node
    # line format: node-id , n , flag , (ptr1,geo1) , (ptr2,geo2) , ...
    # flag = 0 for leaves, 1 for internal nodes
    f = open(path, "w")

    for node in all_nodes: #one line per node, holding:
        nid  = node["node_id"] # node id
        n    = len(node["entries"]) #entry count
        flag = 0 if node["is_leaf"] else 1 #0 for a leaf, 1 for an internal node

        parts = [str(nid), str(n), str(flag)] #str because join() only works with strings

        if node["is_leaf"]:
            # entry = (rid, (x, y))
            for entry in node["entries"]:
                rid = entry[0]
                x   = entry[1][0]
                y   = entry[1][1]
                s = "(" + str(rid) + ",(" + str(x) + ", " + str(y) + "))"
                parts.append(s)
        else:
            # entry = (child_id, [xl, yl, xh, yh])
            for entry in node["entries"]:
                cid = entry[0]
                m   = entry[1]
                s = ("(" + str(cid) + ",["
                     + str(m[0]) + ", " + str(m[1]) + ", "
                     + str(m[2]) + ", " + str(m[3]) + "])")
                parts.append(s)

        f.write(" , ".join(parts) + "\n")

    f.close()

def print_statistics(levels):
    # height = number of levels - 1 (counting edges, not nodes)
    height = len(levels) - 1
    print("Height: " + str(height))

    for i in range(len(levels)): #count how many nodes each level holds
        count = len(levels[i])

        if i == 0:
            avg_area = 0.0   # leaves hold points, not regions -> area = 0
        else:
            total = 0.0
            for node in levels[i]:
                total = total + mbr_area(node["mbr"])
            avg_area = total / count

        print(str(count) + " nodes at level " + str(i) +
              " with average MBR area " + str(avg_area))

def main():
    if len(sys.argv) != 3:
        print("Usage: python Rtree.py <input_file> <output_file>")
        sys.exit(1)

    file_in  = sys.argv[1]
    file_out = sys.argv[2]

    points        = read_points(file_in)
    all_nodes, levels = build_tree(points)
    write_csv(all_nodes, file_out)
    print_statistics(levels)

main()
