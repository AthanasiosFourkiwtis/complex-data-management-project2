# AM:4940 FOURKIOTIS ATHANASIOS
# Perigrafi: k Nearest Neighbor Queries pano sto R-tree.
#            Fortonw to dentro apo CSV, diavazw ta query simeia (qx, qy)
#            kai vriskw tous k plisiesteri geitones gia kathe query.
#            Algorithmos: Incremental Best-First Search me priority queue (heap).
#            Kathe simeio pou vgainei apo tin oura einai o epomenos NN.

import sys
import math
import heapq


def diavase_dentro(path):
    # diavazo to rtree.csv kai ftianxw ton pinaka oloi_oi_komboi
    # indexed by node_id (thesi = id)

    f = open(path, "r")
    grammes = f.readlines()
    f.close()

    oloi_oi_komboi = []

    for grammi in grammes:
        grammi = grammi.strip()
        if grammi == "":
            continue

        meri = grammi.split(" , ")

        node_id = int(meri[0])
        flag    = int(meri[2])
        is_leaf = (flag == 0)

        entries = []

        for i in range(3, len(meri)):
            entry_str = meri[i].strip()
            entry_str = entry_str[1:-1]

            prwti_koma = entry_str.index(",")
            ptr     = int(entry_str[:prwti_koma])
            geo_str = entry_str[prwti_koma + 1:].strip()

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

        kombos = {
            "node_id" : node_id,
            "is_leaf" : is_leaf,
            "entries" : entries
        }
        oloi_oi_komboi.append(kombos)

    return oloi_oi_komboi


def min_dist_simeio_mbr(qx, qy, mbr):
    # Elaxisti apostasi apo to simeio (qx,qy) pros to MBR [xl,yl,xh,yh]
    # Kato frakti: kanena simeio entos MBR den einai pio konta apo afti tin timi

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


def knn_query(oloi_oi_komboi, riza_id, qx, qy, k):
    # Incremental Best-First Search me priority queue
    # Stoixeia heap: (apostasi, monot_aux, typos, id)
    #   typos = 0 -> kombos (node)
    #   typos = 1 -> simeio (leaf entry / record)
    # Kathe simeio pou vgainei apo tin oura einai o epomenos NN
    # Stamatame otan exoume k apotelesmata

    heap  = []
    monot = [0]   # monotonika auxanomenos gia disambiguation tou heapq

    def push_node(nid, dist):
        monot[0] = monot[0] + 1
        heapq.heappush(heap, (dist, monot[0], 0, nid))

    def push_simeio(rid, dist):
        monot[0] = monot[0] + 1
        heapq.heappush(heap, (dist, monot[0], 1, rid))

    # Balo tin riza me apostasi 0.0 (pantote to prwto pou tha vgei)
    push_node(riza_id, 0.0)

    apotelesmata = []   # rids twn k NN me ti seira pou vgainoun

    while len(heap) > 0 and len(apotelesmata) < k:
        d, _, typos, eid = heapq.heappop(heap)

        if typos == 1:
            # Simeio: einai o epomenos plisiesteros geitonas
            apotelesmata.append(eid)
        else:
            # Kombos: ton eksereynw prostethontas ta paidia/simeia tou ston heap
            kombos = oloi_oi_komboi[eid]

            if kombos["is_leaf"]:
                # Fyllo: prosthetw ola ta simeia tou me tin pragmatiki apostasi tous
                for entry in kombos["entries"]:
                    rid  = entry[0]
                    x    = entry[1][0]
                    y    = entry[1][1]
                    dist = math.sqrt((x - qx) * (x - qx) + (y - qy) * (y - qy))
                    push_simeio(rid, dist)
            else:
                # Endiamesos: prosthetw ta paidia tou me tin MINDIST tous
                for entry in kombos["entries"]:
                    child_id  = entry[0]
                    child_mbr = entry[1]
                    d_child   = min_dist_simeio_mbr(qx, qy, child_mbr)
                    push_node(child_id, d_child)

    return apotelesmata


def diavase_queries(path):
    # Kathe grammi: "qx qy" (to simeio-erwtima)

    f = open(path, "r")
    grammes = f.readlines()
    f.close()

    queries = []
    for grammi in grammes:
        grammi = grammi.strip()
        if grammi == "":
            continue
        meri = grammi.split()
        qx = float(meri[0])
        qy = float(meri[1])
        queries.append((qx, qy))

    return queries


def main():
    if len(sys.argv) != 5:
        print("Swsth xrisi: python NNQuery.py <rtree.csv> <NNQueries.txt> <output.txt> <k>")
        sys.exit(1)

    arxeio_tree    = sys.argv[1]
    arxeio_queries = sys.argv[2]
    arxeio_out     = sys.argv[3]
    k              = int(sys.argv[4])

    oloi_oi_komboi = diavase_dentro(arxeio_tree)

    riza_id = oloi_oi_komboi[-1]["node_id"]

    queries = diavase_queries(arxeio_queries)

    f_out = open(arxeio_out, "w")

    for i in range(len(queries)):
        qx, qy = queries[i]

        apotelesmata = knn_query(oloi_oi_komboi, riza_id, qx, qy, k)

        # Morfi eksodou: "i: rid1,rid2,rid3,..."  (xwris arithmo, xwris apostasi)
        str_rids = []
        for rid in apotelesmata:
            str_rids.append(str(rid))
        rids_str = ",".join(str_rids)

        grammi_eksodou = str(i) + ": " + rids_str

        print(grammi_eksodou)
        f_out.write(grammi_eksodou + "\n")

    f_out.close()


main()
