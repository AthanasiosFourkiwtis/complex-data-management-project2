# AM:4940 FOURKIOTIS ATHANASIOS
# Description: Window Range Queries on the R-tree.
#              Loads the tree from CSV, reads the query windows
#              and finds all the points inside each window.

import sys


def read_tree(path):  #rebuilds the R-tree from the csv as a list of nodes
    # read rtree.csv and build the all_nodes list
    # the list is indexed by node_id (position = id, same as in Rtree.py)

    f = open(path, "r") #open rtree.csv and read all the lines
    lines = f.readlines()
    f.close()

    all_nodes = [] #every node I read goes in here

    for line in lines:
        line = line.strip()
        if line == "":
            continue

        # split on " , " (space-comma-space) - that's the field separator
        # e.g. "0 , 51 , 0 , (42474,(39.74118, 116.070466)) , ..."
        parts = line.split(" , ") #a plain .split(",") would also break the commas inside the entries

        node_id = int(parts[0])
        # parts[1] = n (entry count) - not needed separately since the entries get counted at the end
        flag    = int(parts[2])
        if flag == 0:
            is_leaf = True
        else:
            is_leaf = False # 0 = leaf, 1 = internal

        entries = [] #the entries of this node get collected here

        # from parts[3] onward it's the entries
        for i in range(3, len(parts)):
            entry_str = parts[i].strip()

            # every entry looks like: (ptr,geo) with an outer parenthesis
            # e.g. leaf:     (42474,(39.74118, 116.070466))
            # e.g. internal: (1057,[39.680577, 116.070466, 40.179911, 116.547263])
            # strip the outer parenthesis (1st and last char)
            entry_str = entry_str[1:-1] #skip the first and last character

            # find the first comma to split ptr from geo
            # e.g. "42474,(39.74118, 116.070466)" -> first comma at position 5
            first_comma = entry_str.index(",") # index(",") instead of find(",") because a comma is guaranteed, and if it weren't
            #I'd rather the program crash than continue with bad data
            ptr     = int(entry_str[:first_comma]) # everything before the first comma, int() converts it to an integer
            #ptr -> record-id in a leaf, child-node-id in an internal node
            geo_str = entry_str[first_comma + 1:].strip() #everything after the first comma
            #geo_str -> a point in a leaf, an MBR in an internal node

            if is_leaf:
                # geo_str = "(39.74118, 116.070466)"
                # strip the parens and split on ", "
                geo_str = geo_str[1:-1]          # "39.74118, 116.070466"
                coords  = geo_str.split(", ") # split the 2 coordinates, e.g. ["39.74118", "116.070466"]
                x = float(coords[0]) #convert the coordinate strings to numbers
                y = float(coords[1])
                entries.append((ptr, (x, y))) #append the leaf entry; here ptr is the record-id so it's (record-id, (x,y))
            else:
                # geo_str = "[39.682541, 116.070466, 39.74118, 116.119867]"
                # strip the brackets and split on ", "
                geo_str = geo_str[1:-1]          # "39.682541, 116.070466, ..."
                coords  = geo_str.split(", ")
                xl = float(coords[0])
                yl = float(coords[1])
                xh = float(coords[2])
                yh = float(coords[3])  #the bounds of the MBR
                entries.append((ptr, [xl, yl, xh, yh])) #append the entry; here ptr is the child-node-id
                # so it's (child-id, [x_low, y_low, x_high, y_high])

        node = {                   #a dictionary for the node
            "node_id" : node_id,
            "is_leaf" : is_leaf,
            "entries" : entries
        }
        all_nodes.append(node) #add the node to the list of all nodes

    return all_nodes


def mbr_overlaps(mbr, W):
    # Check whether the MBR [xl,yl,xh,yh] overlaps the window W
    # Return False if the MBR is COMPLETELY outside W (in one of the 4 directions)

    # the MBR is completely to the LEFT of W
    if mbr[2] < W[0]:
        return False
    # the MBR is completely to the RIGHT of W
    if mbr[0] > W[2]:
        return False
    # the MBR is completely BELOW W
    if mbr[3] < W[1]:
        return False
    # the MBR is completely ABOVE W
    if mbr[1] > W[3]:
        return False

    return True   # they overlap


def point_inside_W(x, y, W):
    # Check whether the point (x,y) is INSIDE the window W = [x_low,y_low,x_high,y_high]
    if x < W[0] or x > W[2]:
        return False
    if y < W[1] or y > W[3]:
        return False
    return True


def window_query(all_nodes, root_id, W):
    # with a STACK (DFS) from the root
    # Returns a list with all the record_ids found inside the window W

    results = [] #the record-ids that are answers
    stack = [root_id] #start from the root; using a stack means DFS

    while len(stack) > 0:
        nid  = stack.pop()           # take the next node off the stack
        node = all_nodes[nid]

        if node["is_leaf"]:
            # Leaf: check every point against W
            for entry in node["entries"]:
                rid = entry[0]
                x   = entry[1][0]
                y   = entry[1][1]
                if point_inside_W(x, y, W):
                    results.append(rid)
        else:
            # Internal: check each child's MBR
            # If it overlaps W, push it onto the stack to explore it
            for entry in node["entries"]:
                child_id  = entry[0]
                child_mbr = entry[1]
                if mbr_overlaps(child_mbr, W):
                    stack.append(child_id)

    return results


def read_queries(path): #reads every window from the queries file and stores it as [x_low, y_low, x_high, y_high]
    # Read the file with the window queries
    # Each line: "x_low y_low x_high y_high" (4 floats separated by spaces)

    f = open(path, "r")
    lines = f.readlines()
    f.close()

    queries = []
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        parts  = line.split()
        x_low  = float(parts[0])
        y_low  = float(parts[1])
        x_high = float(parts[2])
        y_high = float(parts[3])
        queries.append([x_low, y_low, x_high, y_high])

    return queries


def main():
    if len(sys.argv) != 4:
        print("Usage: python WindowQuery.py <rtree.csv> <windowQueries.txt> <output.txt>")
        sys.exit(1)

    tree_file    = sys.argv[1]
    queries_file = sys.argv[2]
    out_file     = sys.argv[3]

    # Load the R-tree from the CSV
    all_nodes = read_tree(tree_file)

    # The root is the last node (the last thing build_tree produces)
    root_id = all_nodes[-1]["node_id"]
    # print("Root:", root_id, "Total nodes:", len(all_nodes))  # debug

    # Read the query windows
    queries = read_queries(queries_file)

    f_out = open(out_file, "w")

    for i in range(len(queries)):
        W = queries[i]

        results = window_query(all_nodes, root_id, W)

        # Sort the record_ids ascending for easy checking
        results.sort()

        # Build the string with the rids
        str_rids = []
        for r in results:
            str_rids.append(str(r))
        rids_str = ",".join(str_rids)

        # Output format: "i (count): rid1,rid2,..."
        out_line = str(i) + " (" + str(len(results)) + "): " + rids_str

        print(out_line)
        f_out.write(out_line + "\n")

    f_out.close()


main()
