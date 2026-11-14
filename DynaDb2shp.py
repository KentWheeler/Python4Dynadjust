import sqlite3, os
import shapefile as shp
from geodepy.convert import hp2dec, xyz2llh
from geodepy.geodesy import xyz2enu, vincinv


def Create_shp(obs_type):
    dbname='network.db'
    conn = sqlite3.connect(dbname) # or use :memory: to put it in RAM     
    cursor = conn.cursor()
    
    if not os.path.exists(r'shp Layers'):
        os.mkdir(r'shp Layers')
    
    #                0                      1                         2                           3                      4                  5                       6                            7                       8                        9                      10                    11                       12                    13                14                        15
    sql =r"""
    SELECT ADJ_STATION.LATITUDE, ADJ_STATION.LONGITUDE, ADJ_STATION_1.LATITUDE, ADJ_STATION_1.LONGITUDE, ADJ_MEASUREMENT.M, ADJ_MEASUREMENT.ID, ADJ_MEASUREMENT.STATION_1, ADJ_MEASUREMENT.STATION_2, dX.CORRECTION AS X_CORR, dX.N_STAT AS X_N_STAT, dY.CORRECTION AS Y_CORR, dY.N_STAT AS Y_N_STAT, dZ.CORRECTION AS Z_CORR, dZ.N_STAT AS Z_N_STAT, ADJ_MEASUREMENT.N_STAT AS Avg, FILES.FILE_NAME
    FROM 
    (((((ADJ_MEASUREMENT INNER JOIN ADJ_STATION ON (ADJ_MEASUREMENT.STATION_1 = ADJ_STATION.STATION) AND (ADJ_MEASUREMENT.FILES_ID = ADJ_STATION.FILES_ID))  
    INNER JOIN ADJ_STATION AS ADJ_STATION_1 ON (ADJ_MEASUREMENT.STATION_2 = ADJ_STATION_1.STATION) AND (ADJ_MEASUREMENT.FILES_ID = ADJ_STATION_1.FILES_ID)) 
    INNER JOIN 
    (SELECT OBSERVATION_ID, CORRECTION, N_STAT
    FROM X_G_Y_COMPONENTS
    WHERE C='X') AS dX ON ADJ_MEASUREMENT.ID = dX.OBSERVATION_ID) 
    INNER JOIN 
    (SELECT OBSERVATION_ID, CORRECTION, N_STAT
    FROM X_G_Y_COMPONENTS
    WHERE C='Y') AS dY ON ADJ_MEASUREMENT.ID = dY.OBSERVATION_ID) 
    INNER JOIN 
    (SELECT OBSERVATION_ID, CORRECTION, N_STAT
    FROM X_G_Y_COMPONENTS
    WHERE C='Z') AS dZ ON ADJ_MEASUREMENT.ID = dZ.OBSERVATION_ID) 
    INNER JOIN 
    FILES ON ADJ_MEASUREMENT.FILES_ID = FILES.ID
    WHERE ADJ_MEASUREMENT.M = '""" + obs_type +"""'
    ORDER BY ADJ_MEASUREMENT.ID
    """
    
    qry=cursor.execute(sql).fetchall()
    conn.close()
    
    fn = obs_type
    f1 = r'./shp Layers/'+fn+'_line'; w1 = shp.Writer(f1)
    w1.field('M','C')                                    #4
    w1.field('ID','N', size='11', decimal=0)             #5
    w1.field('STN1','C')                                 #6
    w1.field('STN2','C')                                 #7
    w1.field('X_CORR', 'N', decimal=4)                   #8
    w1.field('X_N_STAT', 'N', decimal=2)                 #9
    w1.field('Y_CORR', 'N', decimal=4)                   #10
    w1.field('Y_N_STAT', 'N', decimal=2)                 #11
    w1.field('Z_CORR', 'N', decimal=4)                   #12
    w1.field('Z_N_STAT', 'N', decimal=2)                 #13
    w1.field('Avg', 'N', decimal=2)                      #14
    w1.field('FILENAME','C')                             #15
    w1.field('e_CORR', 'N', decimal=4)                   #16
    w1.field('n_CORR', 'N', decimal=4)                   #17
    w1.field('u_CORR', 'N', decimal=4)                   #18
    
    for row in qry:    
        w1.line([
                [[hp2dec(row[1]), hp2dec(row[0])], 
                  [hp2dec(row[3]), hp2dec(row[2])]]
                ])
        lat=hp2dec(row[2])
        lng=hp2dec(row[3])
        x=row[8]
        y=row[10]
        z=row[12]
        enu=xyz2enu(lat, lng, x, y, z)
        w1.record(row[4], 
                  row[5], 
                  row[6], 
                  row[7], 
                  row[8], 
                  row[9], 
                  row[10], 
                  row[11], 
                  row[12], 
                  row[13], 
                  row[14], 
                  row[15],
                  enu[0],
                  enu[1],
                  enu[2])
    w1.close()


def msr_type2shp(obs_type):
    dbname='network.db'
    conn = sqlite3.connect(dbname) # or use :memory: to put it in RAM     
    cursor = conn.cursor()
    
    if not os.path.exists(r'shp Layers'):
        os.mkdir(r'shp Layers')
    
    #                0                      1                         2                           3                      4                  5                       6                            7                       8                        9                      10                    11                       12                    13                14                        15
    sql =r"""
    SELECT ADJ_STATION.LATITUDE, ADJ_STATION.LONGITUDE, ADJ_STATION_1.LATITUDE, ADJ_STATION_1.LONGITUDE, ADJ_MEASUREMENT.M, ADJ_MEASUREMENT.ID, ADJ_MEASUREMENT.STATION_1, ADJ_MEASUREMENT.STATION_2, dX.CORRECTION AS X_CORR, dX.N_STAT AS X_N_STAT, dY.CORRECTION AS Y_CORR, dY.N_STAT AS Y_N_STAT, dZ.CORRECTION AS Z_CORR, dZ.N_STAT AS Z_N_STAT, ADJ_MEASUREMENT.N_STAT AS Avg, FILES.FILE_NAME
    FROM 
    (((((ADJ_MEASUREMENT INNER JOIN ADJ_STATION ON (ADJ_MEASUREMENT.STATION_1 = ADJ_STATION.STATION) AND (ADJ_MEASUREMENT.FILES_ID = ADJ_STATION.FILES_ID))  
    INNER JOIN ADJ_STATION AS ADJ_STATION_1 ON (ADJ_MEASUREMENT.STATION_2 = ADJ_STATION_1.STATION) AND (ADJ_MEASUREMENT.FILES_ID = ADJ_STATION_1.FILES_ID)) 
    INNER JOIN 
    (SELECT OBSERVATION_ID, CORRECTION, N_STAT
    FROM X_G_Y_COMPONENTS
    WHERE C='X') AS dX ON ADJ_MEASUREMENT.ID = dX.OBSERVATION_ID) 
    INNER JOIN 
    (SELECT OBSERVATION_ID, CORRECTION, N_STAT
    FROM X_G_Y_COMPONENTS
    WHERE C='Y') AS dY ON ADJ_MEASUREMENT.ID = dY.OBSERVATION_ID) 
    INNER JOIN 
    (SELECT OBSERVATION_ID, CORRECTION, N_STAT
    FROM X_G_Y_COMPONENTS
    WHERE C='Z') AS dZ ON ADJ_MEASUREMENT.ID = dZ.OBSERVATION_ID) 
    INNER JOIN 
    FILES ON ADJ_MEASUREMENT.FILES_ID = FILES.ID
    WHERE ADJ_MEASUREMENT.M = '""" + obs_type +"""'
    ORDER BY ADJ_MEASUREMENT.ID
    """
    
    qry=cursor.execute(sql).fetchall()
    conn.close()
    
    fn = obs_type
    f1 = r'./shp Layers/'+fn+'_line'; w1 = shp.Writer(f1)
    w1.field('M','C')                                    #4
    w1.field('ID','N', size='11', decimal=0)             #5
    w1.field('STN1','C')                                 #6
    w1.field('STN2','C')                                 #7
    w1.field('X_CORR', 'N', decimal=4)                   #8
    w1.field('X_N_STAT', 'N', decimal=2)                 #9
    w1.field('Y_CORR', 'N', decimal=4)                   #10
    w1.field('Y_N_STAT', 'N', decimal=2)                 #11
    w1.field('Z_CORR', 'N', decimal=4)                   #12
    w1.field('Z_N_STAT', 'N', decimal=2)                 #13
    w1.field('Avg', 'N', decimal=2)                      #14
    w1.field('FILENAME','C')                             #15
    w1.field('e_CORR', 'N', decimal=4)                   #16
    w1.field('n_CORR', 'N', decimal=4)                   #17
    w1.field('u_CORR', 'N', decimal=4)                   #18
    
    for row in qry:    
        w1.line([
                [[hp2dec(row[1]), hp2dec(row[0])], 
                  [hp2dec(row[3]), hp2dec(row[2])]]
                ])
        lat=hp2dec(row[2])
        lng=hp2dec(row[3])
        x=row[8]
        y=row[10]
        z=row[12]
        enu=xyz2enu(lat, lng, x, y, z)
        w1.record(row[4], 
                  row[5], 
                  row[6], 
                  row[7], 
                  row[8], 
                  row[9], 
                  row[10], 
                  row[11], 
                  row[12], 
                  row[13], 
                  row[14], 
                  row[15],
                  enu[0],
                  enu[1],
                  enu[2])
    w1.close()

def stn_vs_adj2shp():
    dbname='network.db'
    conn = sqlite3.connect(dbname) # or use :memory: to put it in RAM     
    cursor = conn.cursor()
    
    if not os.path.exists(r'shp Layers'):
        os.mkdir(r'shp Layers')
        
    sql = r"""SELECT *
            FROM ADJ_STATION
            JOIN DNA_STATION ON ADJ_STATION.STATION = DNA_STATION.Name;"""

    qry=cursor.execute(sql).fetchall()
    conn.close()
    
    f1 = r'./shp Layers/stn_Vs_adj_point'; w1 = shp.Writer(f1)
    w1.field('STATION','C')                              #4
    w1.field('adj_lat', 'N', decimal=4)                   #8
    w1.field('adj_long', 'N', decimal=2)                 #9
    w1.field('adj_o_ht', 'N', decimal=4)                   #10
    w1.field('adj_e_ht', 'N', decimal=2)                 #11
    w1.field('stn_lat', 'N', decimal=4)                   #12
    w1.field('stn_long', 'N', decimal=2)                 #13
    w1.field('stn_e_ht', 'N', decimal=2)                      #14
    w1.field('hz_shift','C')                             #15
    w1.field('vt_shift', 'N', decimal=4)                   #16
    
    for row in qry:
        if row[21] == 'LLh':
            lat=hp2dec(row[23])
            lng=hp2dec(row[24])
            eHt = row[25]
        if row[21] == 'XYZ':
            lat, lng, eHt = xyz2llh(row[23], row[24], row[25])
            
        hz_shift, _, _ = vincinv(lat,lng,hp2dec(row[6]),hp2dec(row[7]))
        vt_shiff = eHt - row[9]
        w1.point(lng, lat)
        w1.record(row[1], 
                  row[6], 
                  row[7], 
                  row[8], 
                  row[9], 
                  row[23], 
                  row[24], 
                  row[25],
                  hz_shift,
                  vt_shiff)
    w1.close()
    
if __name__ == "__main__":
    Create_shp('X')
    Create_shp('Y')
    Create_shp('G')