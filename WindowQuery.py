# AM:4940 FOURKIOTIS ATHANASIOS
# Perigrafi: Window Range Queries pano sto R-tree.
#            Fortonw to dentro apo CSV, diavazw ta query parathira
#            kai vriskw ola ta simeia pou briskontai mesa se kathe parathiro.

import sys


def diavase_dentro(path):
    # diavazo to rtree.csv kai ftianxw ton pinaka oloi_oi_komboi
    # o pinkas einai indexed by node_id (thesi = id, opws sto Rtree.py)

    f = open(path, "r") #anoigw rtree.csv kai diavazei oles tis grammes
    grammes = f.readlines()
    f.close()

    oloi_oi_komboi = []

    for grammi in grammes:
        grammi = grammi.strip()
        if grammi == "":
            continue

        # xwrizw me " , " (space-koma-space) - auto einai o diaxoristis pediou
        # px "0 , 51 , 0 , (42474,(39.74118, 116.070466)) , ..."
        meri = grammi.split(" , ") #an egrafa .split(",") 8a espage kai ta kommata mesa stis eggrafes

        node_id = int(meri[0])
        # meri[1] = n (plithos entries) - den to xreiazomai ksexwrista afou metraw eggrafes sto telos
        flag    = int(meri[2])
        if flag == 0:
            is_leaf = True
        else:
            is_leaf = False # 0 = fyllo, 1 = endiamesos

        entries = [] #edw mazevw eggrafes aytou tou komvou

        # apo meri[3] kai meta einai ta entries
        for i in range(3, len(meri)):
            entry_str = meri[i].strip()

            # kathe entry exei morfi: (ptr,geo) me exwterikh parenthesi
            # px leaf:     (42474,(39.74118, 116.070466))
            # px internal: (1057,[39.680577, 116.070466, 40.179911, 116.547263])
            # Vgazw thn exwteriki parenthesi (1o kai teleytaio char)
            entry_str = entry_str[1:-1] #agnow prwto kai teleytaio xaraktira

            # Vriskw to prwto koma gia na xwrisw ptr apo geo
            # px "42474,(39.74118, 116.070466)" -> prwto koma sti thesi 5
            prwto_koma = entry_str.index(",") # vazw index(",") kai oxi find(",") gt xerw oti yparxei komma kai an den yphrxe protimw na skasei to programma apo to na synexisei me lathos dedomena
            ptr     = int(entry_str[:prwto_koma]) # ola ta grammata prin to prwto komma kai me to int ginete metatropi se akeraio
            geo_str = entry_str[prwto_koma + 1:].strip() #ola ta grammata meta to prwto komma

            if is_leaf:
                # geo_str = "(39.74118, 116.070466)"
                # Vgazw parenth kai kano split me ", "
                geo_str = geo_str[1:-1]          # "39.74118, 116.070466"
                coords  = geo_str.split(", ")
                x = float(coords[0]) #metatrepw strings se arithmous
                y = float(coords[1])
                entries.append((ptr, (x, y)))
            else:
                # geo_str = "[39.682541, 116.070466, 39.74118, 116.119867]"
                # Vgazw agkistres kai kano split me ", "
                geo_str = geo_str[1:-1]          # "39.682541, 116.070466, ..."
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


def mbr_epikaluptetai(mbr, W):
    # Elegxw an to MBR [xl,yl,xh,yh] epikaluptete me to parathiro W
    # Epistrefw False an to MBR einai TELEIWS ektos tou W (se mia apo tis 4 dieythinseis)

    # to MBR einai teleiws ARISTERA tou W
    if mbr[2] < W[0]:
        return False
    # to MBR einai teleiws DEKSIA tou W
    if mbr[0] > W[2]:
        return False
    # to MBR einai teleiws KATW tou W
    if mbr[3] < W[1]:
        return False
    # to MBR einai teleiws PANW tou W
    if mbr[1] > W[3]:
        return False

    return True   # epikaluptetai


def simeio_mesa_sto_W(x, y, W):
    # Elegxw an to simeio (x,y) einai MESA sto parathiro W = [x_low,y_low,x_high,y_high]
    if x < W[0] or x > W[2]:
        return False
    if y < W[1] or y > W[3]:
        return False
    return True


def window_query(oloi_oi_komboi, riza_id, W):
    # me STIVA (DFS) apo tin riza
    # Epistrefw lista me ola ta record_ids pou vrethikan mesa sto parathiro W

    apotelesmata = []
    stiva = [riza_id] #xekinaw apo thn riza

    while len(stiva) > 0:
        nid    = stiva.pop()           # pairno ton epomeno komvo apo tin stiva
        kombos = oloi_oi_komboi[nid]

        if kombos["is_leaf"]:
            # Fyllo: elegxw kathe simeio an einai mesa sto W
            for entry in kombos["entries"]:
                rid = entry[0]
                x   = entry[1][0]
                y   = entry[1][1]
                if simeio_mesa_sto_W(x, y, W):
                    apotelesmata.append(rid)
        else:
            # Endiamesos: elegxw to MBR kathe paidiou
            # An epikaluptete me W, tote mpainei stiva gia na to eksereynisw
            for entry in kombos["entries"]:
                child_id  = entry[0]
                child_mbr = entry[1]
                if mbr_epikaluptetai(child_mbr, W):
                    stiva.append(child_id)

    return apotelesmata


def diavase_queries(path):
    # Diavazo to arxeio me ta window queries
    # Kathe grammi: "x_low y_low x_high y_high" (4 floats me keno metaksy tous)

    f = open(path, "r")
    grammes = f.readlines()
    f.close()

    queries = []
    for grammi in grammes:
        grammi = grammi.strip()
        if grammi == "":
            continue
        meri   = grammi.split()
        x_low  = float(meri[0])
        y_low  = float(meri[1])
        x_high = float(meri[2])
        y_high = float(meri[3])
        queries.append([x_low, y_low, x_high, y_high])

    return queries


def main():
    if len(sys.argv) != 4:
        print("Swsth xrisi: python WindowQuery.py <rtree.csv> <windowQueries.txt> <output.txt>")
        sys.exit(1)

    arxeio_tree    = sys.argv[1]
    arxeio_queries = sys.argv[2]
    arxeio_out     = sys.argv[3]

    # Fortono to R-tree apo to CSV
    oloi_oi_komboi = diavase_dentro(arxeio_tree)

    # H riza einai o teleytaios kombos (oti dinoume teleutaio sto ftiakse_dentro)
    riza_id = oloi_oi_komboi[-1]["node_id"]
    # print("Riza:", riza_id, "Synolo kombwn:", len(oloi_oi_komboi))  # debug

    # Diavazo ta query parathira
    queries = diavase_queries(arxeio_queries)

    f_out = open(arxeio_out, "w")

    for i in range(len(queries)):
        W = queries[i]

        apotelesmata = window_query(oloi_oi_komboi, riza_id, W)

        # Taxinomw ta record_ids afxouseis gia eukolo elegxo
        apotelesmata.sort()

        # Ftiaxnw to string me ta rids
        str_rids = []
        for r in apotelesmata:
            str_rids.append(str(r))
        rids_str = ",".join(str_rids)

        # Morfi eksodou: "i (count): rid1,rid2,..."
        grammi_eksodou = str(i) + " (" + str(len(apotelesmata)) + "): " + rids_str

        print(grammi_eksodou)
        f_out.write(grammi_eksodou + "\n")

    f_out.close()


main()
