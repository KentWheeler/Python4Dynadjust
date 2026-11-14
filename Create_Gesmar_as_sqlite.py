# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 07:40:32 2026

@author: likdw00
"""

import os
import sqlite3

try:
    import pyodbc
except ImportError as exc:
    raise SystemExit("pyodbc is required. Install it with: pip install pyodbc") from exc
try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit("pandas is required. Install it with: pip install pandas") from exc
    
    
def copy_table(cur, sqlite_conn, table_name, conditions=None):
    print(f"Copying {table_name}...")
    
    sql = f"""
    SELECT *
    FROM GES.{table_name}
    """
    if conditions:
        sql+= f" {conditions}"
    
    df = pd.read_sql(sql, cur.connection)

    df.to_sql(
        table_name,
        sqlite_conn,
        if_exists="replace",
        index=False,
        chunksize=10000
    )

    print(f"  {len(df):,} rows")


def copy_gesmar(cur, sqlite_conn):
    
    tables = [
        ('GES_POINT',"WHERE POINT_TYPE <> 'R'"),
        ('POINT_COORDS',
          """WHERE HORIZ_COORD_STATUS = 'C'
            AND HORIZ_DATUM_NUMBER IN (5,22)"""),
        ('POINT_ACCURACY',"WHERE PROPAGATED_INDICATOR = 'Y'"),
        ('STATUS_HISTORY',None),
        ('ACCESS_DIAGRAM',None),
        ('REDUCED_LEVEL',"WHERE RL_STATUS = 'C'"),
        ('GES_CODES',None),
        ('GES_MAP',None),
        ('HORIZ_DATUM',None),
        ('ADJ_SECTION',None),
        ('GES_ANGLE',None),
        ('ASTRONOMIC_COORDS',None),
        ('GES_AZIMUTH',None),
        ('GES_DISTANCE',None),
        ('GPS_BASELINE',None),
        ('GPS_PRECISION_MATRIX',None),
        ('MULTI_GPS_BASELINE',None),
        ('POINT_NOTES',None),
        ('NON_GS_REFERENCE',None),
        ]
    
    for table, condition in tables:
        copy_table(cur, sqlite_conn, table, condition)
    
    create_indexes(sqlite_conn)
    sqlite_conn.execute("ANALYZE")
    sqlite_conn.commit()


def create_indexes(sqlite_conn):
    cur = sqlite_conn.cursor()

    indexes = [

        # GES_POINT
        """
        CREATE INDEX IF NOT EXISTS idx_gp_point
        ON GES_POINT (POINT_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_gp_type
        ON GES_POINT (POINT_TYPE)
        """,

        # POINT_COORDS
        """
        CREATE INDEX IF NOT EXISTS idx_pc_point
        ON POINT_COORDS (POINT_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_pc_datum
        ON POINT_COORDS (HORIZ_DATUM_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_pc_point_datum
        ON POINT_COORDS (
            POINT_NUMBER,
            HORIZ_DATUM_NUMBER,
            HORIZ_COORD_STATUS
        )
        """,

        # POINT_ACCURACY
        """
        CREATE INDEX IF NOT EXISTS idx_pa_point
        ON POINT_ACCURACY (POINT_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_pa_coord
        ON POINT_ACCURACY (
            POINT_NUMBER,
            SECTION_NUMBER,
            COORDINATE_NUMBER
        )
        """,

        # STATUS_HISTORY
        """
        CREATE INDEX IF NOT EXISTS idx_sh_point
        ON STATUS_HISTORY (POINT_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_sh_point_date
        ON STATUS_HISTORY (
            POINT_NUMBER,
            STATUS_DATE DESC
        )
        """,

        # ACCESS_DIAGRAM
        """
        CREATE INDEX IF NOT EXISTS idx_ad_point
        ON ACCESS_DIAGRAM (POINT_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_ad_point_version
        ON ACCESS_DIAGRAM (
            POINT_NUMBER,
            VERSION_NUMBER DESC
        )
        """,

        # REDUCED_LEVEL
        """
        CREATE INDEX IF NOT EXISTS idx_rl_point
        ON REDUCED_LEVEL (POINT_NUMBER)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_rl_datum
        ON REDUCED_LEVEL (
            POINT_NUMBER,
            RL_TYPE,
            RL_STATUS,
            VERT_DATUM_NUMBER
        )
        """,

        # GES_CODES
        """
        CREATE INDEX IF NOT EXISTS idx_gc_code_number
        ON GES_CODES (CODE_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gc_code
        ON GES_CODES (CODE);
        """,
        
        # GES_MAP
        """
        CREATE INDEX IF NOT EXISTS idx_gm_map_record
        ON GES_MAP (MAP_RECORD_NUMBER);
        """,
        
        # GES_MAP
        """
        CREATE INDEX IF NOT EXISTS idx_ga_at
        ON GES_ANGLE (AT_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ga_from
        ON GES_ANGLE (FROM_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ga_to
        ON GES_ANGLE (TO_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ga_angle_number
        ON GES_ANGLE (ANGLE_NUMBER);
        """,
        
        # GES_AZIMUTH
        """
        CREATE INDEX IF NOT EXISTS idx_gaz_at
        ON GES_AZIMUTH (AT_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gaz_to
        ON GES_AZIMUTH (TO_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gaz_number
        ON GES_AZIMUTH (AZIMUTH_NUMBER);
        """,
        
        # GES_DISTANCE
        """
        CREATE INDEX IF NOT EXISTS idx_gd_from
        ON GES_DISTANCE (FROM_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gd_to
        ON GES_DISTANCE (TO_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gd_number
        ON GES_DISTANCE (DISTANCE_NUMBER);
        """,
        
        # GPS_BASELINE
        """
        CREATE INDEX IF NOT EXISTS idx_gps_group
        ON GPS_BASELINE (BASELINE_GROUP_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gps_at
        ON GPS_BASELINE (AT_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gps_to
        ON GPS_BASELINE (TO_POINT_NUMBER);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gps_number
        ON GPS_BASELINE (BASELINE_NUMBER);
        """,
        
        # GPS_PRECISION_MATRIX
        """
        CREATE INDEX IF NOT EXISTS idx_gpm_group
        ON GPS_PRECISION_MATRIX (BASELINE_GROUP_NUMBER);        
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_gpm_group_row_col
        ON GPS_PRECISION_MATRIX
        (
            BASELINE_GROUP_NUMBER,
            MATRIX_ROW_NUMBER,
            MATRIX_COLUMN_NUMBER
        );
        """,
        
        # MULTI_GPS_BASELINE
        """
        CREATE INDEX IF NOT EXISTS idx_mgps_group
        ON MULTI_GPS_BASELINE (BASELINE_GROUP_NUMBER);
        """,
        
        # POINT_NOTES
        """
        CREATE INDEX IF NOT EXISTS idx_notes_point
        ON POINT_NOTES (POINT_NUMBER);
        """,
        
        # GES_POINT
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_gp_point_unique
        ON GES_POINT (POINT_NUMBER);
        """,
        
        # NON_GS_REFERENCE
        """
        CREATE INDEX IF NOT EXISTS idx_ngs_point
        ON NON_GS_REFERENCE (POINT_NUMBER);
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_ngs_id
        ON NON_GS_REFERENCE (NON_GS_NUMBER);
        """,
        ]

    for sql in indexes:
        cur.execute(sql)

    sqlite_conn.commit()
    print("Indexes created")


def Gesmar2sqlite(
        driver=os.environ.get("GES_DRIVER"),
        dbq="LDGAPPP1", 
        user=os.environ.get("USERNAME"), 
        password=os.environ.get("GESMAR_PWD"),
        out="gesmar_sqlite.db"):
    print("Connecting to GESMAR...")
    
    connection_str = f"DRIVER={{{driver}}};DBQ={dbq};UID={user};PWD={password}"
    with pyodbc.connect(connection_str) as cnxn:
        with sqlite3.connect(out) as sqlite_conn:
            copy_gesmar(cnxn.cursor(), sqlite_conn)
            


if __name__ == "__main__":
    Gesmar2sqlite()