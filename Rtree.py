# AM:4940 FOURKIOTIS ATHANASIOS
# Perigrafi: Diavazw simeia apo arxeio, ftiaxnw R-tree me STR bulk loading
#            sti mnimi, to grafoume se CSV kai typonw statistika.

import sys
import math

# STATHERES
# Kathe kombos = 1024 bytes
# Fyllo   : rid(4B) + x(8B) + y(8B) = 20B -> MAX = floor(1024/20) = 51
# Endiames: nid(4B) + 4*8B (MBR) = 36B    -> MAX = floor(1024/36) = 28
# MIN = 40% tou MAX (kanones R-tree gia na min exoume adeioys kombous)

MAX_LEAF = 51
MAX_INT  = 28
MIN_LEAF = 20   # floor(0.4 * 51) = 20
MIN_INT  = 11   # floor(0.4 * 28) = 11


def vres_mbr_simeiwn(lista_simeiwn):
    # pairnei lista apo (x,y) kai epistrefei to [x_low,_low,x_high,y_high]
    x_low  = lista_simeiwn[0][0]
    x_high = lista_simeiwn[0][0]
    y_low  = lista_simeiwn[0][1]
    y_high = lista_simeiwn[0][1]

    for s in lista_simeiwn:
        if s[0] < x_low:
            x_low = s[0]
        if s[0] > x_high:
            x_high = s[0]
        if s[1] < y_low:
            y_low = s[1]
        if s[1] > y_high:
            y_high = s[1]

    return [x_low, y_low, x_high, y_high]


def vres_mbr_kombwn(lista_mbr):
    # idia logiki, alla eisodos einai lista apo MBRs (oxi simeia)
    # to xreiazomai otan ftiaxnw gonea afou to MBR tou xwraei ola ta MBR twn paidiwn
    x_low  = lista_mbr[0][0]
    y_low  = lista_mbr[0][1]
    x_high = lista_mbr[0][2]
    y_high = lista_mbr[0][3]

    for m in lista_mbr:
        if m[0] < x_low:
            x_low = m[0]
        if m[1] < y_low:
            y_low = m[1]
        if m[2] > x_high:
            x_high = m[2]
        if m[3] > y_high:
            y_high = m[3]

    return [x_low, y_low, x_high, y_high]


def embado_mbr(mbr):
    return (mbr[2] - mbr[0]) * (mbr[3] - mbr[1]) #πλάτος = x_high - x_low
                                                 #ύψος = y_high - y_low
                                                 #εμβαδόν = πλάτος * ύψος


def diavase_simeia(path): #diavazei Beijing_restaurants.txt
    # prwti grammi = plithos (to agnooume, diavazoume osa vroume)
    # kathe alli grammi: "x y"
    f = open(path, "r")
    grammes = f.readlines()
    f.close()

    simeia = [] #adeia lista gia ta shmeia
    for i in range(1, len(grammes)): #ksekinaw apo 1 oxi apo 0 afou h grammi 0 einai to plh8os(51970)
        g = grammes[i].strip() #vgazw ta /n sto telos
        if g == "":   #an grammi kenh thn paraleipw
            continue
        meri = g.split() # px "39.856 116.423"->.split()->["39.856", "116.423"]->float()->(39.856, 116.423)-> x=39.856 kai y=116.423
        x = float(meri[0]) #meri[0],meri[1] einai string kai den mporw na kanw mathimatika se strings ara to kanw float
        y = float(meri[1])
        simeia.append((x, y)) # dipli parenthesi gt thelw na prosthesw ena tuple kai oxi 2 orismata opote tha eskage gt h append pernei 1 orisma

    return simeia

def xwrise_se_groups(lista, megethos): # xrhsimopoieitai gia na kopsw ta shmeia se fylla twn 51 h komvous se omades twn 28
    # spao ti lista se ypolistes twn 'megethos' stoixeiwn
    # to teleutaio group mporei na exei ligotero
    # p.x. [1,2,3,4,5], megethos=2  ->  [[1,2], [3,4], [5]]
    groups = []
    trexon_group = []
    for stoixeio in lista:
        trexon_group.append(stoixeio)
        if len(trexon_group) == megethos:
            groups.append(trexon_group)
            trexon_group = []
    
    # Gia to teleytaio group an einai mikrotero tou "megethos"
    if len(trexon_group) > 0:
        groups.append(trexon_group)
    
    return groups


def diorthwse_underflow(groups, elaxisto):
    # an o teleytaios kombos exei ligoteres eggrafes apo to elaxisto,
    # "kleboume" stoixeia apo ton protelevtaio
    # exairesi: mono 1 group = riza, den kanoume tipota

    if len(groups) < 2:
        return groups # an exw 1 group dhladh riza den kanw tipota kathws h riza ekseiritai apo to minimum

    teleytaios = groups[-1]

    if len(teleytaios) >= elaxisto:
        return groups   # ola ok

    # posa stoixeia xreiazomai na prosthesw
    leipoun = elaxisto - len(teleytaios)
    protelevtaios = groups[-2]

    # pairnoume ta teleytaia 'leipoun' stoixeia tou protelevtaiou
    ta_extra = protelevtaios[-leipoun:] 
    groups[-2] = protelevtaios[:-leipoun] # antikatestise to proteleutaio group me ola ta stoixeia ektos apo ta teleutaia 'leipoun'
    groups[-1] = ta_extra + teleytaios #Antikatestise to teleytaio group me ta ta_extra (pou metefera) + ta stoixeia pou eixe hdh.
      # edw einai ta_extra + teleutaios kai oxi teleytaios + ta_extra Giati ta stoixeia einai taksinomhmena kata y (apo to STR). Το orfano shmeio 
      #exei to megaliero y sto dataset. Ta ta_extra (teleutaia tou proteleutaiou) exoun mikrotero y apo to orfano alla megalitero apo ta stoixeia pou emeinan sto proteleutaio.
   
   # print("underflow fix: teleytaios tora exei", len(groups[-1]))  # debug
    return groups

def key_x_simeio(eggrafi):
    # eggrafi = (record_id, (x, y)) -> epistrefei x gia taksinomisi
    return eggrafi[1][0]


def key_y_simeio(eggrafi):
    # epistrefei y gia taksinomisi
    return eggrafi[1][1]
 # oi 2 parapanw einai voithitikes synarthseis poy lene sthn sorted me vasi poia syntetagmenh na taksinomhsei
 
def str_pack_fylla(eggrafes): #pairnei eggrafes kai epistrfei omades pou tha ginoun fylla
    # eggrafes = lista apo (record_id, (x,y))
    # epistrefei lista apo groups -> kathe group tha ginei ena fyllo

    N = len(eggrafes) # an den yparxoun shmeia epestrepse kenh lista
    if N == 0:
        return []

    # posa fylla xreiazomai
    P = math.ceil(N / MAX_LEAF)
    # poses kathetes lwrides -> theloume tetragwna "tiles" sti xwrika
    S = math.ceil(math.sqrt(P))
    if S < 1:
        S = 1

    # print("fylla: N =", N, " P =", P, " S =", S)  # debug

    # Vima 1: taksinomisi kata x (apo aristera pros ta deksia ston xarti)
    sortd_x = sorted(eggrafes, key=key_x_simeio)

    # Vima 2: kopsimo se S kathetes lwrides(kathe lwrida = S*MAX_LEAF stoixeia)
    lwrides = xwrise_se_groups(sortd_x, S * MAX_LEAF)

    # Vima 3: se kathe lwrida, taksinomisi kata y kai prosthetw stin teliki lista
    teliki = []
    for lwrida in lwrides:
        sortd_y = sorted(lwrida, key=key_y_simeio)
        for eg in sortd_y:
            teliki.append(eg)

    # Vima 4: kopsimo se groups MAX_LEAF + diorthwsi underflow
    groups = xwrise_se_groups(teliki, MAX_LEAF)
    groups = diorthwse_underflow(groups, MIN_LEAF)

    return groups

def key_x_kombou(kombos):
    # epistrefei to kentro_x tou MBR tou kombou (gia taksinomisi)
    mbr = kombos["mbr"]
    return (mbr[0] + mbr[2]) / 2.0


def key_y_kombou(kombos):
    # epistrefei to kentro_y tou MBR tou kombou (gia taksinomisi)
    mbr = kombos["mbr"]
    return (mbr[1] + mbr[3]) / 2.0

def str_pack_kombwn(lista_kombwn):
    # idia logiki me str_pack_fylla, alla gia kombous-paidia
    # Taksinomisi kata KENTRO MBR (oxi gwnia)

    N = len(lista_kombwn)
    if N == 0:
        return []

    P = math.ceil(N / MAX_INT)
    S = math.ceil(math.sqrt(P))
    if S < 1:
        S = 1

    # Vima 1: taksinomisi kata kentro_x tou MBR
    sortd_x = sorted(lista_kombwn, key=key_x_kombou)

    # Vima 2: kopsimo se kathetes lwrides
    lwrides = xwrise_se_groups(sortd_x, S * MAX_INT)

    # Vima 3: se kathe lwrida, taksinomisi kata kentro_y
    teliki = []
    for lwrida in lwrides:
        sortd_y = sorted(lwrida, key=key_y_kombou)
        for k in sortd_y:
            teliki.append(k)

    # Vima 4: kopsimo se groups MAX_INT + diorthwsi underflow
    groups = xwrise_se_groups(teliki, MAX_INT)
    groups = diorthwse_underflow(groups, MIN_INT)

    return groups

def ftiakse_dentro(simeia): # dhmiourgei filla me str kai meta epanaliptika dhmiourgei goneis. kathe goneas apothikeuei ta node-ids kai mbr twn paidiwn tou kai h diadikasia stamata otan menei enas komvos dhladh h riza.
    # record_id = grammi sto arxeio, ksekinaei apo 1
    eggrafes = []
    for i in range(len(simeia)): # edw dinw record-id se kathe shmeio 
        rid = i + 1
        eggrafes.append((rid, simeia[i]))

    # oi komboi mpainoun se lista - i thesi tous einai to node_id
    # prosomionei array sto disko
    oloi_oi_komboi = []
    epipeda = []        # gia statistika

    # ===== EPIPEDO 0: fylla (STR) =====
    groups_fyllwn = str_pack_fylla(eggrafes)
    epipedo_0 = []

    for group in groups_fyllwn:
        node_id = len(oloi_oi_komboi)   # thesi komvou sthn lysta

        # MBR tou fyllou apo ta simeia tou
        simeia_group = []
        for eg in group:
            simeia_group.append(eg[1])
        mbr = vres_mbr_simeiwn(simeia_group)

        fyllo = {
            "node_id" : node_id,
            "is_leaf" : True,
            "entries" : group,    # lista apo (rid, (x,y))
            "mbr"     : mbr
        }
        oloi_oi_komboi.append(fyllo)
        epipedo_0.append(fyllo)

    epipeda.append(epipedo_0)
    # print("Epipedo 0:", len(epipedo_0), "fylla")  # debug

    # ===== EPIPEDA 1, 2, ... mexri riza (bulk loading, xwris taksinomisi) =====
    trexon = epipedo_0

    while len(trexon) > 1: #oso exw panw apo 1 komvo prepei na ftiaksw goneis
        groups_kombwn = str_pack_kombwn(trexon)
        #anti gia grammi 262 na eixa grammi 263,264
       # groups_kombwn = xwrise_se_groups(trexon, MAX_INT)
       #groups_kombwn = diorthwse_underflow(groups_kombwn, MIN_INT)
        epomeno = []

        for group in groups_kombwn: # gia kathe omada paidiwn ftiaxnw enan gonea
            node_id = len(oloi_oi_komboi) #dinw node-id ston neo komvo

            entries = [] # ayto pou tha apothikeysei o endiamesos komvos
            mbrs_paidiwn = [] # gia na ypologisw mbr gonea
            for paidi in group:
                entries.append((paidi["node_id"], paidi["mbr"])) # gia kathe paidi apothikevw node-id kai mbr
                mbrs_paidiwn.append(paidi["mbr"])

            mbr = vres_mbr_kombwn(mbrs_paidiwn)

            kombos = {
                "node_id" : node_id,
                "is_leaf" : False,
                "entries" : entries,   # lista apo (child_id, mbr_paidiou)
                "mbr"     : mbr
            }
            oloi_oi_komboi.append(kombos)
            epomeno.append(kombos)

        epipeda.append(epomeno)
        # print("Neo epipedo:", len(epomeno), "komboi")  # debug
        trexon = epomeno

    return oloi_oi_komboi, epipeda

def grapse_csv(oloi_oi_komboi, path): #grafei to Rtree se arxeio, mia grammi an komvo
    # morfi grammi: node-id , n , flag , (ptr1,geo1) , (ptr2,geo2) , ...
    # flag = 0 gia fylla, 1 gia endiamesous
    f = open(path, "w")

    for kombos in oloi_oi_komboi: #gia kathe komvo grafeis mia grammi me:
        nid  = kombos["node_id"] # id komvou
        n    = len(kombos["entries"]) #plhthos egrafwn
        flag = 0 if kombos["is_leaf"] else 1 #0 gia fyllo ,1 gia endiameso

        kommatia = [str(nid), str(n), str(flag)] #str afou h join() doulevei mono me strings

        if kombos["is_leaf"]:
            # entry = (rid, (x, y))
            for entry in kombos["entries"]:
                rid = entry[0]
                x   = entry[1][0]
                y   = entry[1][1]
                s = "(" + str(rid) + ",(" + str(x) + ", " + str(y) + "))"
                kommatia.append(s)
        else:
            # entry = (child_id, [xl, yl, xh, yh])
            for entry in kombos["entries"]:
                cid = entry[0]
                m   = entry[1]
                s = ("(" + str(cid) + ",["
                     + str(m[0]) + ", " + str(m[1]) + ", "
                     + str(m[2]) + ", " + str(m[3]) + "])")
                kommatia.append(s)

        f.write(" , ".join(kommatia) + "\n")

    f.close()

def typwse_statistika(epipeda):
    # ypsos = arithmos epipedwn - 1 (metraw akmees, oxi kombous)
    ypsos = len(epipeda) - 1
    print("Height: " + str(ypsos))

    for i in range(len(epipeda)): #gia kathe epipedo metraw posoi komvoi yparxoun
        plithos = len(epipeda[i])

        if i == 0:
            meso_embado = 0.0   # fylla exoun simeia, oxi perioxi -> embado = 0
        else:
            athroisma = 0.0
            for kombos in epipeda[i]:
                athroisma = athroisma + embado_mbr(kombos["mbr"])
            meso_embado = athroisma / plithos

        print(str(plithos) + " nodes at level " + str(i) +
              " with average MBR area " + str(meso_embado))

def main():
    if len(sys.argv) != 3:
        print("H Swsth Xrisi einai : python Rtree.py <arxeio_eisodou> <arxeio_eksodou>")
        sys.exit(1)

    arxeio_in  = sys.argv[1]
    arxeio_out = sys.argv[2]

    simeia                  = diavase_simeia(arxeio_in)
    oloi_oi_komboi, epipeda = ftiakse_dentro(simeia)
    grapse_csv(oloi_oi_komboi, arxeio_out)
    typwse_statistika(epipeda)

main() 