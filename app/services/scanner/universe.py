"""Symbols scanned on every run, before the day's most-active and biggest movers are added.

These are liquid, heavily traded option chains: index and sector ETFs, mega-caps, and the
single names that regularly lead options volume.
"""

DEFAULT_UNIVERSE: tuple[str, ...] = (
    "SPY", "QQQ", "IWM", "DIA", "NVDA", "TSLA", "AAPL", "AMZN", "META", "MSFT",
    "GOOGL", "GOOG", "AMD", "PLTR", "AVGO", "NFLX", "MSTR", "COIN", "HOOD", "SOFI",
    "INTC", "MU", "SMCI", "BABA", "BAC", "JPM", "C", "WFC", "GS", "F",
    "GM", "NIO", "RIVN", "LCID", "UBER", "DIS", "XOM", "CVX", "OXY", "GLD",
    "SLV", "TLT", "HYG", "XLF", "XLE", "SMH", "SOXL", "TQQQ", "SQQQ", "UVXY",
    "VXX", "ARM", "ORCL", "CRM", "ADBE", "SHOP", "SNOW", "CRWD", "PANW", "NKE",
    "BA", "UNH", "LLY", "PFE", "WMT", "COST", "TGT", "PYPL", "XYZ", "RBLX",
    "SNAP", "PINS", "MARA", "RIOT", "CLSK", "IBIT", "ETHA", "GME", "AMC", "CVNA",
    "DKNG", "AFRM", "UPST", "RDDT", "APP", "CRWV", "OKLO", "IONQ", "RGTI", "QBTS",
    "SMR", "ASTS", "RKLB", "LULU", "TSM", "ASML", "QCOM", "TXN", "MRVL", "DELL",
    "HIMS", "NVO", "CELH", "FXI", "EEM", "KRE", "XBI", "ARKK", "GDX", "USO",
    "UNG", "T", "VZ", "KO", "PEP", "MCD", "SBUX", "ABNB", "CCL", "AAL",
    "DAL", "UAL", "CMG", "V", "MA", "IBM", "CSCO", "NOW", "ZS", "NET",
    "DDOG", "MDB", "U", "AI", "SOUN", "BBAI", "TEM", "NBIS", "CIFR", "IREN",
    "WULF", "HUT", "BMNR", "SBET", "CRCL", "FIG", "JOBY", "ACHR", "LUNR", "NVTS",
    "ENPH", "FSLR", "RUN", "SEDG", "MRNA", "BIDU", "JD", "PDD", "LI", "XPEV",
)
