import os, sqlite3
import xmltodict
from geodepy.geodesy import xyz2enu
import shapefile as shp
from collections import OrderedDict
import argparse
import sys

## Functions in this file ##
# delete_DynaML_db
# create_DynaML_db
# add_tbl_clm
# fmt4sql
# list2sql
# add_file_ref
# stn_xml2db
# msr_xml2db
# import_adj
# import_apu
default_sql = (
    """
    m.*,

    s1.LATITUDE   AS GEO_STN1_LAT,
    s1.LONGITUDE AS GEO_STN1_LON,

    s2.LATITUDE   AS GEO_STN2_LAT,
    s2.LONGITUDE AS GEO_STN2_LON,

    s3.LATITUDE   AS GEO_STN3_LAT,
    s3.LONGITUDE AS GEO_STN3_LON

FROM ADJ_MEASUREMENT AS m

LEFT JOIN ADJ_STATION AS s1
    ON m.STATION_1 = s1.STATION
	AND m.FILES_ID = s1.FILES_ID

LEFT JOIN ADJ_STATION AS s2
    ON m.STATION_2 = s2.STATION
	AND m.FILES_ID = s2.FILES_ID

LEFT JOIN ADJ_STATION AS s3
    ON m.STATION_3 = s3.STATION
	AND m.FILES_ID = s3.FILES_ID""")
    
LAYERS_SQL = {
    "Azimuths_TYPE_B_K":
        f"{default_sql} WHERE m.M IN ('B', 'K');",
    "Distances_TYPE_C_E_M_S":
        f"{default_sql} WHERE m.M IN ('C', 'E', 'M', 'S');",
    "Height_Diff_TYPE_L":
        f"{default_sql} WHERE m.M IN ('L');",
    "Heights_TYPE_H_R":
        f"{default_sql} WHERE m.M IN ('H', 'R');",
    "Astro_TYPE_P_Q_I_J":
        f"{default_sql} WHERE m.M IN ('P', 'Q', 'I', 'J');",
    }
def delete_DynaML_db(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS FILES')
    cursor.execute('DROP TABLE IF EXISTS DNA_STATION')
    cursor.execute('DROP TABLE IF EXISTS DNA_MEASUREMENT')
    cursor.execute('DROP TABLE IF EXISTS DNA_BASELINES')
    cursor.execute('DROP TABLE IF EXISTS DNA_DIRECTIONS')
    cursor.execute('DROP TABLE IF EXISTS ADJ_STATION')
    cursor.execute('DROP TABLE IF EXISTS ADJ_MEASUREMENT')
    cursor.execute('DROP TABLE IF EXISTS ADJ_ADJUSTMENT_STATS')
    cursor.execute('DROP TABLE IF EXISTS X_G_Y_COMPONENTS')
    cursor.execute('DROP TABLE IF EXISTS APU_STATION')
    conn.commit()
    conn.close()

def create_DynaML_db(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS FILES (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS DNA_STATION (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS DNA_MEASUREMENT (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS DNA_BASELINES (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS DNA_DIRECTIONS (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ADJ_STATION (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ADJ_MEASUREMENT (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ADJ_ADJUSTMENT_STATS (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS X_G_Y_COMPONENTS (
                  ID integer PRIMARY KEY);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS APU_STATION (
                  ID integer PRIMARY KEY);''')

    conn.commit()
    conn.close()


def add_tbl_clm(tbl,clms,conn):
    cursor = conn.cursor()
    e_clms=cursor.execute('PRAGMA table_info('+tbl+')').fetchall()
    for c in clms:
        add_c=True
        if c =='': add_c=False
        for e in e_clms:
            if c in e: add_c=False
        if add_c==True:
            sql='ALTER TABLE ' + tbl + ' ADD '
            sql= sql + c
            if (c =='M' 
                or c.startswith('STATION') 
                or c =='C' or c =='OUTLIER?' 
                or c =='CONST' 
                or c == 'DESCRIPTION'):
                sql = sql + ' short text;'
            else:
                sql = sql + ' double;'
            cursor.execute(sql)
            conn.commit()
        
        
def fmt4sql(stg):
    stg=(stg.replace('*',' ')
            .replace('. ID','_ID ')
            .replace('?',' ')
            .replace('.','')
            .replace('-','_')
            .replace('(','_')
            .replace(',','_')
            .replace(':',' ')
            .replace('%','p')
            .replace(')',' ')
            .replace('M Station 1','M  Station 1')
            .upper())
    clms=[s.strip().replace(' ','_') for s in stg.split('  ') if s]
    return clms


def list2sql (clms):
    sql = ' ('
    v=''
    for c in clms:
        sql=sql + c + ', '
        v = v + '?,'
    sql = sql[:-2] + ') VALUES ('+v[:-1] +')'     
    return sql


def add_file_ref(f,tbl,conn):
    cursor = conn.cursor()
    add_tbl_clm(tbl,['FILES_ID'],conn)
    add_tbl_clm('FILES',['FILE_NAME'],conn)
    fle_id = cursor.execute("SELECT ID FROM FILES WHERE FILE_NAME = '" 
                            + f + "'").fetchall()
    if len(fle_id)==0:
        cursor.execute('''INSERT INTO FILES (FILE_NAME)
                        VALUES (?)''',[f])
        fle_id = cursor.execute("SELECT MAX(ID) FROM FILES").fetchall()

    cursor.execute('UPDATE '+tbl+ \
                   ' set FILES_ID='+ str(fle_id[0][0]) + \
                   ' WHERE FILES_ID is null')
    conn.commit()    
    
def stn_xml2db (f,db):  
    ######## Open the station file 
    ##         create table columns
    ##         add all the station fields to one table
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    with open(f, 'r') as x:
        xml = xmltodict.parse(
            x.read(),
            process_comments=True,
            comment_key='COMMENT'
        )

    clms=[]
    for stn in xml['DnaXmlFormat']['DnaStation']:
        dta_stn=[]
        stn.update(stn['StationCoord'])
        for k in stn:
            if k!='StationCoord':
                dta_stn=dta_stn+[stn[k]]
                if k not in clms:
                    add_tbl_clm('DNA_STATION',[k],conn)
                    clms=clms+[k]
        sql =list2sql(clms)
        cursor.execute('INSERT INTO DNA_STATION '+sql, dta_stn)
    conn.commit()
    # Add the file name as a reference
    add_file_ref(f,'DNA_STATION',conn)
    conn.close()
    

def msr_xml2db(f,db):
    ######## Open the msr file 
    ##         create table columns
    ##         every measurement is given a measurement number
    ##         every measurement is added to the DNA_MEASUREMENT table
    ##         the components of Directions and GNSS baselines are added to the DNA_DIRECTIONS and DNA_BASELINES tables
    with open(f, 'r') as x:
        xml = xmltodict.parse(x.read())

    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    msr_cnt= cursor.execute("SELECT MAX(ID) FROM DNA_MEASUREMENT").fetchall()[0][0]
    if msr_cnt==None: msr_cnt=0
    add_tbl_clm('DNA_BASELINES',['MEASUREMENT_ID'],conn)
    add_tbl_clm('DNA_DIRECTIONS',['MEASUREMENT_ID'],conn)
    m = xml['DnaXmlFormat']['DnaMeasurement']
    if type(m)!=list: m=[m]
    for msr in m:
        clms=[]
        dta=[]
        msr_cnt+=1
        for ky, msr_val in msr.items():
            if ky=='Directions':
                if isinstance(msr_val, dict):
                    msr_val = [msr_val]
                for tgt in msr_val:
                    add_tbl_clm('DNA_DIRECTIONS',list(tgt.keys()),conn)
                    sql =list2sql(['MEASUREMENT_ID']+list(tgt.keys()))
                    cursor.execute('INSERT INTO DNA_DIRECTIONS '+
                                   sql, [msr_cnt]+list(tgt.values()))
            
            elif ky=='GPSBaseline' or ky=='Clusterpoint':
                add_tbl_clm('DNA_BASELINES',list(msr_val.keys()),conn)
                sql =list2sql(['MEASUREMENT_ID']+list(msr_val.keys()))
                cursor.execute('INSERT INTO DNA_BASELINES '+
                               sql, [msr_cnt]+list(msr_val.values()))
                
            else:
                if ky not in clms: 
                    add_tbl_clm('DNA_MEASUREMENT',[ky],conn)
                    clms=clms+[ky]
                dta=dta + [msr_val]
        sql =list2sql(clms)
        cursor.execute('INSERT INTO DNA_MEASUREMENT '+
                       sql, dta)
        
    conn.commit()
    # Add the file name as a reference
    add_file_ref(f,'DNA_MEASUREMENT',conn)
    conn.close()


def import_adj(f,db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    obs_id = cursor.execute("SELECT MAX(ID) FROM ADJ_MEASUREMENT").fetchall()[0][0]
    if obs_id==None: obs_id=0
    obs_id+=1
    gnss_p=[]
    tbl=''
    adj_stats={}
    adj_stns={}
    adj_obs={}
    c_ln=-1
    with open(f, 'r') as adj_f:    
        for ln in adj_f.readlines():
            # Pause and skip line reading if following is true
            if (ln.strip()=='/n' 
             or ln.strip()==''
             or ln.startswith('    ')): continue
            if ln.startswith('+ Initialising adjustment'): c_ln=-1
            if ln.startswith('Adjusted Coordinates'): c_ln=-1
            if ln.startswith('Measurements to Station'): c_ln=-1
            if ln.startswith('Adjusted Measurements'): c_ln=-1

            # Read in the adjustment Stats
            if ln.startswith('DYNADJUST ADJUSTMENT OUTPUT FILE'):
                tbl='ADJ_ADJUSTMENT_STATS'
                stats_clms=[]; dta=[]
                c_ln=2
            if ln.startswith('SOLUTION'):
                c_ln=0
            if (c_ln == 0 and tbl=='ADJ_ADJUSTMENT_STATS' 
                and ln.startswith('--')==False):
                c_n_d = fmt4sql(ln)
                stats_clms = stats_clms + [c_n_d[0]]
                dta = dta + [ln[ln.find('  '):].strip()]
            if ln.startswith('Adjusted Measurements'):
                add_tbl_clm(tbl,stats_clms,conn)
                sql =list2sql(stats_clms)
                cursor.execute('INSERT INTO ' +tbl+ ' ' +sql, dta)
                for c, d in zip(stats_clms,dta): adj_stats.update({c:d})
                
            # Read in the coordinates (Stop at EOF)
            if ln.startswith('Station             Const'):
                tbl='ADJ_STATION'
                clms=fmt4sql(ln)
                add_tbl_clm(tbl ,clms,conn)
                c_ln=2
            if c_ln == 0 and tbl=='ADJ_STATION':
                dta=[ln[:20].strip()]
                dta=dta + ln[20:].split()
                # join description if split by spaces
                if len(dta)>len(clms): 
                    desc=' '.join(dta[len(clms)-1:])
                    dta=dta[:len(clms)]
                    dta[len(clms)-1]=desc
                sql =list2sql(clms[:len(dta)])
                cursor.execute('INSERT INTO ' +tbl+ ' ' +sql, dta)
                adj_stns[dta[0]]={}
                for c, d in zip(clms,dta): adj_stns[dta[0]].update({c:d})
            
            # Read in the measurements (Stop at 'Adjusted Coordinates')
            if ln.startswith('M Station 1           Station 2           Station 3'):
                tbl='ADJ_MEASUREMENT'
                clms=fmt4sql(ln)
                add_tbl_clm('ADJ_MEASUREMENT' ,clms,conn)
                add_tbl_clm('X_G_Y_COMPONENTS' ,
                            ['OBSERVATION_ID'] + fmt4sql(ln[65:]),conn)
                c_ln=2
                i=0
            if c_ln == 0 and tbl=='ADJ_MEASUREMENT':
                dta=[ln[:2].strip()] 
                dta.append(ln[2:20].strip())    #First
                dta.append(ln[22:40].strip())   #second
                dta.append(ln[42:60].strip())   #third
                dta.append(ln[62:67].strip())   #C
                for e in [s.strip() for s in ln[68:106].split('  ') if s]:
                    try: dta.append(float(e))
                    except ValueError: dta.append(e)
                for e in [s.strip() for s in ln[106:].split(' ') if s]:
                    try: dta.append(float(e))
                    except ValueError: dta.append(e)
                
                adj_obs[i]={'OBS_ID':obs_id}
                for c, d in zip(clms,dta): adj_obs[i].update({c:d})
                i+=1
                
                if dta[0] == 'X' or dta[0] == 'Y' or dta[0] == 'G':
                    xgy=[obs_id]+dta[4:]                  
                    sql =list2sql(['OBSERVATION_ID']+clms[4:len(xgy)+3])
                    cursor.execute('INSERT INTO X_G_Y_COMPONENTS '+sql, xgy)
                    gnss_p.append(dta)
                    if len(gnss_p)==3:
                        dta[4]='Avg'
                        for c in range(5,7):
                            dta[c]=''
                        for c in range(7,len(gnss_p[0])-2):
                            avg_xgy=sum(abs(row[c]) for row in gnss_p if row[c]!='*')/3
                            dta[c]=round(avg_xgy,4)
                        gnss_p=[]

                if len(gnss_p)==0:
                    sql = list2sql(clms[:len(dta)])
                    cursor.execute('INSERT INTO ADJ_MEASUREMENT '+sql, dta)
                    obs_id+=1
                
            if c_ln > 0: c_ln-=1
    conn.commit()
    # Add the file name as a reference
    add_file_ref(f,'ADJ_ADJUSTMENT_STATS',conn)
    add_file_ref(f,'ADJ_STATION',conn)
    add_file_ref(f,'ADJ_MEASUREMENT',conn)
    conn.close()
    
    return adj_stats, adj_stns, adj_obs


def import_apu(f,db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    c_ln = -1
    apu_stns={}
    with open(f, 'r') as apu_f:    
        for ln in apu_f.readlines():
            if ln=='\n': c_ln=-1
            if ln.startswith(
                    'Station                     Latitude      Longitude    Hz PosU    Vt PosU   Semi-major   Semi-minor  Orientation        Variance(X)        Variance(Y)        Variance(Z)'
                    ):
                clms = fmt4sql(ln)
                add_tbl_clm('APU_STATION', clms, conn)
                c_ln = 2
            if c_ln == 0:
                stn = [ln[:20].strip()]         #Station
                stn = stn + ln[20:].split()     #Latitude...  etc
                sql = list2sql(clms)
                cursor.execute('INSERT INTO APU_STATION '+sql, stn)
                apu_stns[stn[0]]={}
                for c, d in zip(clms,stn): apu_stns[stn[0]].update({c:d})
                c_ln=3
            if c_ln > 0: c_ln-=1
    conn.commit()

    # Add the file name as a reference
    add_file_ref(f,'APU_STATION',conn)           
    conn.close()
    
    return apu_stns
    

def count_sigfigs(n):
    mpl = 1
    sf = 0
    while int(n*mpl) != n*mpl:
        mpl = mpl * 10
        sf += 1
    return sf


def isnumber(x):
    if not x: return False
    try:
        float(x)
        return True
    except ValueError:
        return False


def defineshpfields(k, v, clms):
    if k not in clms.keys():
        if isnumber(v):
            v = float(v)
            clms[k] = (
                {'name': k, 
                 'type': 'N', 
                 'size': len(str(v)),
                 'decimal':count_sigfigs(v)})
        else:
            clms[k] = {'name': k, 'type': 'C'}
    else:
        if clms[k]['type'] == 'N':
            v = float(v)
            if len(str(v)) > clms[k]['size']: clms[k]['size'] = len(str(v))
            if count_sigfigs(v) >clms[k]['decimal']:
                clms[k]['decimal'] = count_sigfigs(v)
    return clms
    
    
def dynaml2shp (f,db):  
    if not os.path.exists(r'shp Layers'):
        os.mkdir(r'shp Layers')
    
    nulllist=[]
    while len(nulllist)<30:
        nulllist.append('')        
    stns = {}
    ######## Open the station file 
    if f.endswith('stn.xml'):
        with open(f, 'r') as x:
            xml = xmltodict.parse(x.read())
    
        for stn in xml['DnaXmlFormat']['DnaStation']:
            for k, v in stn.items():
                if k != 'StationCoord':
                    if not stn['Name'] in stns.keys(): stns[stn['Name']]={}
                    stns[stn['Name']][k] = v
                else:
                    for k2, v2 in stn['StationCoord'].items():
                        stns[stn['Name']][k2] = v2
        
        clms = {'Name':{'name':'Name', 'type': 'C'}}
        for stn in stns.values():
            for k, v in stn.items():
                clms = defineshpfields(k, v, clms)
            
        f1 = r'./shp Layers/'+f.replace('.','_')+'_point'
        w1 = shp.Writer(f1)
        for c in clms.values():
             if c['type'] == 'N':
                 w1.field(c['name'], c['type'], 
                          size = str(c['size']), decimal = c['decimal'])
             else:
                 w1.field(c['name'], c['type'])
        
        for stn in stns.values():
            w1.point(
                float(stn['XAxis']),
                float(stn['YAxis']))

            pnt_record = nulllist        
            for k, v in stn.items():
                pnt_record[list(clms.keys()).index(k)] = v
                
            w1.record(
                pnt_record[0],
                pnt_record[1],
                pnt_record[2],
                pnt_record[3],
                pnt_record[4],
                pnt_record[5],
                pnt_record[6],
                pnt_record[7],
                pnt_record[8],
                pnt_record[9],
                pnt_record[10])
        w1.close()
    
    ######## Open the measure file if it exists
    if os.path.exists(f.replace('stn.xml','msr.xml')):
        with open(f.replace('stn.xml','msr.xml'), 'r') as x:
            xml = xmltodict.parse(x.read())
        
        clms = {}
        msrs = []
        for msr in xml['DnaXmlFormat']['DnaMeasurement']:
            elemts ={}
            for k, v in msr.items():
                if k == 'Clusterpoint':
                    for k2, v2 in msr['Clusterpoint'].items():
                        elemts[k2] = v2
                elif k == 'GPSBaseline':
                    for k2, v2 in msr['GPSBaseline'].items():
                        elemts[k2] = v2
                elif k == 'Directions':
                    for k2, v2 in msr['Directions'].items():
                        elemts[k2] = v2
                else:
                    elemts[k] = v
            msrs.append(elemts)
    
        clms = OrderedDict({
                'First':{'name':'First', 'type': 'C'},
                'Second':{'name':'Second', 'type': 'C'},
                'Target':{'name':'Target', 'type': 'C'}})
        for msr in msrs:
            for k, v in msr.items():
                clms = defineshpfields(k, v, clms)
        
        f1 = r'./shp Layers/' + f.replace('stn.xml','msr.xml').replace('.','_') + '_line'
        w1 = shp.Writer(f1)
        for c in clms.values():
            if c['type'] == 'N':
                w1.field(c['name'], c['type'], 
                         size = str(c['size']), decimal = c['decimal'])
            else:
                w1.field(c['name'], c['type'])
        
        for msr in msrs:
            if 'Target' in msr.keys():
                w1.line([[
                    [float(stns[msr['First']]['XAxis']), float(stns[msr['First']]['YAxis'])],
                    [float(stns[msr['Second']]['XAxis']),float(stns[msr['Second']]['YAxis'])],
                    [float(stns[msr['Target']]['XAxis']),float(stns[msr['Target']]['YAxis'])]
                    ]])
            elif 'Second' in msr.keys():
                w1.line([[
                    [float(stns[msr['First']]['XAxis']), float(stns[msr['First']]['YAxis'])],
                    [float(stns[msr['Second']]['XAxis']),float(stns[msr['Second']]['YAxis'])]
                    ]])
            elif 'First' in msr.keys():
                w1.line([[
                    [float(stns[msr['First']]['XAxis']), float(stns[msr['First']]['YAxis'])],
                    [float(stns[msr['First']]['XAxis']),float(stns[msr['First']]['YAxis'])]
                    ]])
            
            pnt_record = nulllist        
            for k, v in msr.items():
                pnt_record[list(clms.keys()).index(k)] = v
            
            w1.record(
                pnt_record[0],
                pnt_record[1],
                pnt_record[2],
                pnt_record[3],
                pnt_record[4],
                pnt_record[5],
                pnt_record[6],
                pnt_record[7],
                pnt_record[8],
                pnt_record[9],
                pnt_record[10],
                pnt_record[11],
                pnt_record[12],
                pnt_record[13],
                pnt_record[14],
                pnt_record[15],
                pnt_record[16],
                pnt_record[17],
                pnt_record[18],
                pnt_record[19],
                pnt_record[20],
                pnt_record[21],
                pnt_record[22],
                pnt_record[23],
                pnt_record[24],
                pnt_record[25],
                pnt_record[26],
                pnt_record[27],
                pnt_record[28],
                pnt_record[29],)
        w1.close()
 
        
def parse_args():
     ap = argparse.ArgumentParser(description="Import adjustment files into a database.")
     ap.add_argument("--stn", required=False, help="DynaML station xml file (.stn.xml)")
     ap.add_argument("--msr", required=False, help="DynaML measure xml file (.msr.xml)")
     ap.add_argument("--adj", required=False, help="DynAdjust adjustment file (.adj)")
     ap.add_argument("--apu", required=False,  help="DynAdjust positional uncertainty file (.apu)")

     ap.add_argument("--stn2", required=False, help="Second DynaML station xml file (.stn.xml)")
     ap.add_argument("--msr2", required=False, help="Second DynaML measure xml file (.msr.xml)")
     ap.add_argument("--adj2", required=False, help="Second DynAdjust adjustment file (.adj)")
     ap.add_argument("--apu2", required=False,  help="Second DynAdjust positional uncertainty file (.apu)")

     return ap.parse_args()
 
    
if __name__ == "__main__":
    script_path = os.path.abspath(os.path.realpath(__file__))
    script_dir, script_name = os.path.split(script_path)
    os.chdir(script_dir)
    db='network.db'
    delete_DynaML_db(db)
    create_DynaML_db(db)
    args = parse_args()
    
    if args.stn:
        stn_xml2db (args.stn, db)
    if args.msr:
        stn_xml2db (args.msr, db)
    if args.adj:
        stn_xml2db (args.adj, db)
    if args.apu:
        stn_xml2db (args.apu, db)
    if args.stn2:
        stn_xml2db (args.stn2, db)
    if args.msr2:
        stn_xml2db (args.msr2, db)
    if args.adj2:
        stn_xml2db (args.adj2, db)
    if args.apu2:
        stn_xml2db (args.apu2, db)
        
    ######### Create a default database when there are no arguments ############
    if len(sys.argv) == 1:
        files = os.listdir('.')
        for file in files:
            if file.endswith('.stn.xml'):
                stn_xml2db (file, db)
    
            if file.endswith('msr.xml'):
                msr_xml2db (file, db)
                
            if file.endswith('.adj'):
                import_adj (file, db)
                
            if file.endswith('.apu'):
                import_apu (file, db) 
            
            
    
    

