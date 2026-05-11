# AM:4940 FOURKIOTIS ATHANASIOS
# Perigrafi: Distance Range Queries pano sto R-tree.
#            Fortonw to dentro apo CSV, diavazw ta query (qx, qy, r)
#            kai vriskw ola ta simeia entos apostasis r apo to (qx, qy).

import sys
import math


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
    # Vriskw to eggytero simeio panw sto MBR kai ypologizw tin apostasi

    xl = mbr[0]
    yl = mbr[1]
    xh = mbr[2]
    yh = mbr[3]

    # Eggytero x panw sto [xl, xh]
    if qx < xl:
        cx = xl
    elif qx > xh:
        cx = xh
    else:
        cx = qx

    # Eggytero y panw sto [yl, yh]
    if qy < yl:
        cy = yl
    elif qy > yh:
        cy = yh
    else:
        cy = qy

    dx = qx - cx
    dy = qy - cy
    return math.sqrt(dx * dx + dy * dy)


def distance_query(oloi_oi_komboi, riza_id, qx, qy, r):
    # DFS me stiva
    # Epistrefw lista me ola ta record_ids pou exoun apostasi <= r apo (qx, qy)

    apotelesmata = []
    stiva = [riza_id]

    while len(stiva) > 0:
        nid    = stiva.pop()
        kombos = oloi_oi_komboi[nid]

        if kombos["is_leaf"]:
            # Fyllo: elegxw kathe simeio
            for entry in kombos["entries"]:
                rid = entry[0]
                x   = entry[1][0]
                y   = entry[1][1]
                dist = math.sqrt((x - qx) * (x - qx) + (y - qy) * (y - qy))
                if dist <= r:
                    apotelesmata.append(rid)
        else:
            # Endiamesos: elegxw an to MBR kathe paidiou temnei tin sfaira aposatsis r
            # Monopatia me MINDIST(simeio, MBR) > r den mporoun na periexoun simeia entos r
            for entry in kombos["entries"]:
                child_id  = entry[0]
                child_mbr = entry[1]
                if min_dist_simeio_mbr(qx, qy, child_mbr) <= r:
                    stiva.append(child_id)

    return apotelesmata


def diavase_queries(path):
    # Kathe grammi: "qx qy r" (kentro kai aktina)

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
        r  = float(meri[2])
        queries.append((qx, qy, r))

    return queries


def main():
    if len(sys.argv) != 4:
        print("Swsth xrisi: python DistanceQuery.py <rtree.csv> <distanceQueries.txt> <output.txt>")
        sys.exit(1)

    arxeio_tree    = sys.argv[1]
    arxeio_queries = sys.argv[2]
    arxeio_out     = sys.argv[3]

    oloi_oi_komboi = diavase_dentro(arxeio_tree)

    riza_id = oloi_oi_komboi[-1]["node_id"]

    queries = diavase_queries(arxeio_queries)

    f_out = open(arxeio_out, "w")

    for i in range(len(queries)):
        qx, qy, r = queries[i]

        apotelesmata = distance_query(oloi_oi_komboi, riza_id, qx, qy, r)

        apotelesmata.sort()

        str_rids = []
        for rid in apotelesmata:
            str_rids.append(str(rid))
        rids_str = ",".join(str_rids)

        grammi_eksodou = str(i) + " (" + str(len(apotelesmata)) + "): " + rids_str

        print(grammi_eksodou)
        f_out.write(grammi_eksodou + "\n")

    f_out.close()


main()
