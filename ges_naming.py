# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 07:47:38 2026

@author: likdw00


Useful methods for
Mapsheet name <-> code lookup and GEODETIC_POINT_NAME -> SHORT_NAME logic.
 - dspl_nme(nme: str | None) -> str | None
 - ges_short_name(mk_name: str | None) -> str | None:
 - full_ges_name

"""

# ---------------------------------------------------------------------------
# Variable for mapsheets
# ---------------------------------------------------------------------------

MAPSHEET_NAMES: tuple[str, ...] = (
    "ABYSSINIA", "ALLANSON", "APPLECROSS", "ARMADALE", "ASHENDON", "AUSTRALIND", "BALGA", "BANKSIA",
    "BARTONS", "BAYSWATER", "BECHER", "BERRIJUP", "BICKLEY", "BALD", "BAILUP", "BELLEVUE",
    "BAILEY", "BALMORAL", "BOORONGING", "BOONGARRA", "BOUVARD", "BLUE ROCK", "BRIDGETOWN NE", "BRIDGETOWN NW",
    "BRIDGETOWN SE", "BRIDGETOWN SW", "BULLSBROOK", "BURNS", "BELVIDERE", "BYFORD", "BUNBURY NORTH", "BUNBURY SOUTH",
    "CALISTA", "CANNINGTON", "CARILLA", "CAVERSHAM", "COBBLER", "CARCOOLA", "CHIDLOW", "CLIFFORD",
    "CHANDALA", "CHEDARING", "CHURCHMAN", "CITY", "COOKE", "CLAREMONT", "CLENTON", "CLOVER",
    "CUTLER", "COCKMAN", "CHINGANNING", "COOGEE", "CURTIS", "CANNINGVALE", "DALE", "DARKIN",
    "DAWESVILLE", "DEEFOR", "DANDALUP", "DARDANUP", "DOCONING", "DALYELLUP", "EAGLE", "EAST YANCHEP",
    "FERGUS", "FERGUSON", "FLORIDA", "FORRESTDALE", "FREMANTLE", "FISHER", "GIBBS", "GLENCAIRN",
    "GLEN FORREST", "GUILDFORD", "GIDGEGANNUP", "GARDEN ISLAND", "GREENLANDS", "GOLDMINE", "GNANGARA", "GOBBY",
    "GORRY", "GOSNELLS", "GULL", "HAMERSLEY", "HANCOCK", "HADDRILL", "HELENA EAST", "HERNE HILL",
    "HODD", "HERRON", "HERRON WEST", "HARRIS", "HASTIES", "HUNTLY", "JANDAKOT", "JARRAHDALE",
    "JIB", "JULIMAR", "JUMPERKINE", "KALAMUNDA", "KARNUP", "KOOMBANA", "KINGSBURY", "KELMSCOTT",
    "KENNEDY", "KEWDALE", "KEYSBROOK", "KARNET", "KRONIN", "KEATING", "KWINANA", "LAKE ADAMS",
    "LAWLEY", "LIGHTBODY", "LAKE CARABOODA", "LEONA", "LESMURDIE", "LAKE JANDABUP", "LESCHENAULT", "LOWLANDS",
    "MAGENUP", "MANDOGALUP", "MANDURAH NE", "MANDURAH NW", "MARSH", "MANDURAH SE", "MANDURAH SW", "MUNDARING",
    "MUNDIJONG", "MEALUP", "MELVILLE", "MUNGALUP", "MT HELENA", "MIAMI", "MALKUP", "MOONDYNE",
    "MORANGUP", "MADDERN", "MARRIOTT", "MARYVILLE", "MULLALOO", "MUCHEA NORTH", "MUCHEA SOUTH", "MAIDA VALE",
    "MYARA", "NAMBEELUP", "NAVAL BASE", "NEERABUP", "MC NESS", "NETTLETON", "NORTHAM EAST", "NORTHAM WEST",
    "NOCKINE", "OAKLEY", "OBRIEN", "OMEO", "PARKERVILLE", "PERON", "PAGE", "PICKERING",
    "PIESSE", "PINJAR EAST", "PINJAR WEST", "PEEL", "PEELHURST", "PHILLIPS", "POISON", "PUNRACK",
    "QUININE", "QUINNS NORTH", "QUINNS SOUTH", "RANDALL", "RUEN", "ROCKINGHAM", "ROLAND", "ROLEYSTONE",
    "ROSSMOYNE", "ROTTNEST ISLAND", "RAVENSWOOD", "SAFETY BAY", "SCARBOROUGH", "SOUTH CHITTERING", "SERPENTINE", "SINGLETON",
    "SMITHS MILL", "SOLUS", "SPRINGVALE", "SAWPIT", "SPEARWOOD", "SCARP", "STONY", "SUNSET",
    "STONEVILLE", "TOODYAY", "THOMPSON", "THORNLIE", "TURTLE", "TOMAR", "THORPE", "TWO ROCKS NORTH",
    "TWO ROCKS SOUTH", "UPPER SWAN", "VENN", "VINCENT", "WAHRONGA", "WALYUNGA", "WANNEROO", "WARNBRO",
    "WARBROOK", "WEST BYFORD", "WUNDOWIE", "WEIR", "WELLARD", "WEMBLEY", "WERRIBEE", "WESTCOTT",
    "WHITFORDS", "WILTON", "WATERLOO", "WOONGANING", "WOODSOME", "WOOROLOO", "WOTNOT", "WANDARRAH",
    "WARIIN", "WEST SWAN", "WORSLEY", "WEST TOODYAY", "WESTONS", "WUNGONG", "WEST YANCHEP", "YAKAMINDI",
    "YANGEDI", "YEAL", "YETAR", "YALGORUP", "YALGORUP WEST", "YOKINE", "YUNDERUP", "AJANA",
    "ALBANY", "ANKETELL", "ASHTON", "AUGUSTA", "BALLADONIA", "BOORABBIN", "BREMER BAY", "BENCUBBIN",
    "BEDOUT ISLAND", "BELELE", "BENTLEY", "BALFOUR DOWNS", "BILLILUNA", "BARLEE", "BULLEN", "BURNABBIE",
    "BROWNE", "BROOME", "BROWSE ISLAND", "BARROW ISLAND", "BUSSELTON", "BYRO", "CAMBRIDGE GULF", "CAMDEN SOUND",
    "CUNDEELEE", "CROSSLAND", "CHARNLEY", "CORNISH", "COBB", "COCOS ISLAND", "COLLIE", "COLLIER",
    "CORRIGIN", "CAPE ARID", "COOPER", "CHRISTMAS", "CUE", "CULVER", "DAMPIER", "DERBY",
    "DIXON RANGE", "DUMMER", "DONGARA", "DRYSDALE", "DUKETON", "DUMBLEYUNG", "EDJUDINA", "EDEL",
    "EDMUND", "ESPERANCE", "EUCLA", "FORREST", "GORDON DOWNS", "GLENGARRY", "GLENBURGH", "GERALDTON",
    "GUNANYA", "HELENA", "HERBERT", "HILL RIVER", "HYDEN", "IRWIN INLET", "JACKSON", "JOANNA SPRING",
    "JUBILEE", "KALGOORLIE", "KELLERBERRIN", "KIRKALOCKA", "KENNEDY RANGE", "KINGSTON", "KURNALPI", "LAGRANGE",
    "LANSDOWNE", "LAVERTON", "LENNARD RIVER", "LEONORA", "LISSADELL", "LAKE JOHNSTON", "LOONGANA", "LENNIS",
    "LONDONDERRY", "LUCAS", "MARBLE BAR", "MADLEY", "MALCOLM", "MOUNT BRUCE", "MOUNT BARKER", "MACDONALD",
    "MCLARTY HILLS", "MANDORA", "MONDRAIN ISLAND", "MADURA", "MEDUSA BANKS", "MINIGWAL", "MINILYA", "MENZIES",
    "MONTAGUE SOUND", "MOUNT PHILLIPS", "MOORA", "MOUNT RAMSAY", "MURGOO", "MUNRO", "MORRIS", "MASON",
    "MOUNT ANDERSON", "MOUNT BANNERMAN", "MOUNT ELIZABETH", "MOUNT EGERTON", "NABBERU", "NARETHA", "NEWDEGATE", "NINGALOO",
    "NINGHAN", "NORTH KEELING", "NEALE", "NOONKANBAH", "NORSEMAN", "NOONAERA", "NULLAGINE", "NEWMAN",
    "ONSLOW", "PERCIVAL", "PEMBERTON", "PENDER", "PORT HEDLAND", "PINJARRA", "PEAK HILL", "PLUMRIDGE",
    "PATERSON RANGE", "PERENJORI", "PRINCE REGENT", "PERTH", "PYRAMID", "QUOBBA", "RAVENSTHORPE", "RAWLINSON",
    "ROBERT", "ROY HILL", "ROBERTSON", "ROEBOURNE", "ROBINSON RANGE", "RASON", "RUDALL", "RUNTON",
    "RYAN", "SAHARA", "SIR SAMUEL", "SANDSTONE", "SOUTHERN CROSS", "SCOTT", "SEEMORE", "SHARK BAY",
    "STANLEY", "STANSMORE", "TALBOT", "TABLETOP", "TRAINOR", "THROSSELL", "TUREE CREEK", "URAL",
    "VERNON", "WEBB", "WAIGEN", "WIDGIEMOOLTHA", "WOORAMEL", "WILUNA", "WANNA", "WINNING POOL",
    "WARRI", "WILSON", "WESTWOOD", "WYLOO", "YALGOO", "YAMPI", "YARINGA", "YARRALOOLA",
    "YOUANMI", "YOWALGA", "YARRIE", "YANREY", "ZANTHUS", "ASHMORE REEF", "HIBERNIA REEF", "LONG REEF",
    "HOUTMAN ABROLHOS",)

MAPSHEET_CODES: tuple[str, ...] = (
    "ABY", "ALN", "APP", "ARM", "ASH", "AUS", "BAL", "BAN",
    "BAR", "BAYS", "BEC", "BER", "BIC", "BLD", "BLP", "BLV",
    "BLY", "BML", "BOO", "BOON", "BOU", "BRK", "BTNE", "BTNW",
    "BTSE", "BTSW", "BUL", "BURN", "BVR", "BYF", "BYN", "BYS",
    "CAL", "CAN", "CAR", "CAV", "CBR", "CCA", "CDW", "CFD",
    "CHA", "CHE", "CHUR", "CITY", "CKE", "CLAR", "CLN", "CLO",
    "CLR", "CMN", "CNG", "COO", "CUR", "CVAL", "DAL", "DAR",
    "DAW", "DEE", "DLP", "DNP", "DOC", "DYP", "EAG", "EYAN",
    "FER", "FGN", "FLO", "FOR", "FRE", "FSR", "GBS", "GCN",
    "GF", "GFD", "GID", "GIS", "GLS", "GM", "GNAN", "GOB",
    "GOR", "GOS", "GUL", "HAM", "HAN", "HDL", "HLE", "HNH",
    "HOD", "HRN", "HRNW", "HRS", "HTS", "HTY", "JAN", "JAR",
    "JIB", "JUL", "JUM", "KAL", "KAR", "KBA", "KBY", "KELM",
    "KEN", "KEW", "KEY", "KNT", "KRN", "KTG", "KWIN", "LAD",
    "LAW", "LBY", "LCAR", "LEO", "LES", "LJAN", "LNT", "LOW",
    "MAG", "MAN", "MANE", "MANW", "MAR", "MASE", "MASW", "MDG",
    "MDJ", "MEA", "MEL", "MGP", "MHEL", "MIA", "MKP", "MOO",
    "MOR", "MRN", "MRT", "MRY", "MULL", "MUN", "MUS", "MV",
    "MYA", "NAM", "NAV", "NEE", "NESS", "NET", "NME", "NMW",
    "NOC", "OAK", "OBR", "OME", "PAR", "PER", "PGE", "PIC",
    "PIE", "PINE", "PINW", "PL", "PLH", "PLP", "PSN", "PUN",
    "QNE", "QUN", "QUS", "RDL", "REN", "ROC", "ROD", "ROL",
    "ROSS", "ROT", "RWD", "SB", "SCA", "SCH", "SER", "SGTN",
    "SMM", "SOL", "SPR", "SPT", "SPW", "SRP", "STY", "SUN",
    "SVLE", "TDY", "THOM", "THOR", "TLE", "TOM", "TPE", "TRN",
    "TRS", "USW", "VEN", "VIN", "WAH", "WAL", "WAN", "WAR",
    "WBK", "WBYF", "WDE", "WEIR", "WEL", "WEM", "WER", "WES",
    "WHIT", "WIL", "WLO", "WNG", "WOO", "WOR", "WOT", "WRH",
    "WRN", "WSW", "WSY", "WTDY", "WTN", "WUN", "WYAN", "YAK",
    "YAN", "YEAL", "YET", "YGP", "YGPW", "YOK", "YUN", "AJA",
    "ALB", "ANK", "ATN", "AUG", "BALA", "BBN", "BBY", "BCN",
    "BED", "BEL", "BEN", "BFD", "BIL", "BLE", "BLN", "BNB",
    "BRN", "BRO", "BRS", "BRW", "BUS", "BYR", "CAG", "CAM",
    "CDE", "CLD", "CLY", "CNH", "COB", "COC", "COL", "COLR",
    "COR", "CPA", "CPR", "CRI", "CUE", "CUL", "DAM", "DBY",
    "DIX", "DMR", "DON", "DRY", "DUK", "DUM", "EDA", "EDL",
    "EMD", "ESP", "EUC", "FST", "GDNS", "GGY", "GLB", "GN",
    "GUN", "HEL", "HER", "HLR", "HYD", "IRW", "JAK", "JSP",
    "JUB", "KB", "KE", "KIRK", "KRE", "KTN", "KURN", "LAG",
    "LAN", "LAV", "LDR", "LEN", "LIS", "LJ", "LNA", "LNS",
    "LON", "LUC", "MAB", "MAD", "MAL", "MBC", "MBR", "MCD",
    "MCH", "MDA", "MDN", "MDU", "MED", "MGL", "MIN", "MNZ",
    "MON", "MPH", "MRA", "MRAM", "MRG", "MRO", "MRS", "MSN",
    "MTA", "MTB", "MTE", "MTG", "NAB", "NAR", "NEW", "NGL",
    "NIN", "NK", "NLE", "NOON", "NOR", "NRA", "NUL", "NWM",
    "ONS", "PCL", "PEM", "PEN", "PH", "PIN", "PKH", "PLUM",
    "PRA", "PRJ", "PRT", "PTH", "PYR", "QUO", "RAV", "RAW",
    "RBT", "RHL", "ROB", "ROE", "RRA", "RSN", "RUD", "RUN",
    "RYN", "SAH", "SAM", "SAN", "SC", "SCT", "SEE", "SKB",
    "SLY", "SMR", "TAL", "TLT", "TNR", "TSL", "TUR", "URL",
    "VER", "WEB", "WGN", "WID", "WML", "WNA", "WNN", "WPL",
    "WRR", "WSN", "WWD", "WYL", "YAL", "YAM", "YAR", "YLA",
    "YOU", "YOW", "YRE", "YRY", "ZAN", "ARF", "HRF", "LOR",
    "ABR",)

_MAPSHEET_NAME_TO_CODE: dict[str, str] = dict(zip(MAPSHEET_NAMES, MAPSHEET_CODES))
_MAPSHEET_CODE_TO_NAME: dict[str, str] = dict(zip(MAPSHEET_CODES, MAPSHEET_NAMES))
# Both directions are unique (checked at build time: no mapsheet name or code
# repeats), so the reverse dict is lossless -- unlike a naive "first match
# wins" linear scan would risk being if that assumption ever broke.


def dspl_nme(nme: str ) -> str :
    """Port of VBA DsplNme(): insert a space wherever a letter is
    immediately followed by a digit, e.g. "MDJ12BM1" -> "MDJ 12BM 1".
    """
    if nme is None:
        return None
    nme = str(nme).strip()
    if not nme:
        return nme

    out = [nme[0]]
    for i in range(1, len(nme)):
        prev_ch = nme[i - 1]
        ch = nme[i]
        if ch.isdigit() and prev_ch.isalpha():
            out.append(" ")
        out.append(ch)

    return "".join(out).upper().strip()


def ges_short_name(mk_name: str) -> str:
    """Port of VBA AbbName(): replace the mapsheet-name prefix of a mark name
    with its abbreviation code, e.g. "MUNDIJONG12BM1" -> "MDJ12BM1".

    The mapsheet portion is taken as the leading run of characters up to
    (but not including) the first digit. If that leading text matches a
    known mapsheet name exactly, all occurrences of it in the name are
    replaced with the corresponding code (matching VBA's Replace() call,
    which replaces every occurrence, not just the first).

    Unlike the VBA version, which linearly scans the 425-entry mapsheet
    array on every call, this looks the name up in a dict built once at
    import time -- O(1) instead of O(n) per call.
    """
    if mk_name is None:
        return None
    mk_name = str(mk_name).strip().upper()
    mk_name = dspl_nme(mk_name)
    if not mk_name:
        return mk_name

    mapsheet_name = None
    for i in range(1, len(mk_name)):
        if mk_name[i].isdigit():
            mapsheet_name = mk_name[:i].strip()
            break

    if mapsheet_name:
        code = _MAPSHEET_NAME_TO_CODE.get(mapsheet_name)
        if code:
            return mk_name.replace(mapsheet_name, code)

    return mk_name


def full_ges_name(short_name: str) -> str:
    """Port of VBA FullGESName(): the reverse of abb_name() -- replace a
    mapsheet code prefix with its full name, e.g. "MDJ12BM1" -> "MUNDIJONG12BM1".

    Also accepts a space-formatted SHORT_NAME (dspl_nme() output, e.g.
    "MDJ 12BM 1") by stripping spaces before matching, since dspl_nme()
    only ever inserts spaces and never changes any other character --
    removing them recovers the exact abb_name() form.

    Uses the same O(1) dict lookup as abb_name(), built once at import time
    instead of scanning the mapsheet array on every call.
    """
    if short_name is None:
        return None
    nme = str(short_name).replace(" ", "").strip().upper()    
    nme = dspl_nme(nme)
    if not nme:
        return nme

    map_code = None
    for i in range(1, len(nme)):
        if nme[i].isdigit():
            map_code = nme[:i].strip()
            break

    if map_code:
        name = _MAPSHEET_CODE_TO_NAME.get(map_code)
        if name:
            return nme.replace(map_code, name)

    return nme
