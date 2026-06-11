DOMAIN = "vab"

# EFA (Bahnland Bayern) – deckt VAB/Aschaffenburg ab
EFA_BASE_URL = "https://bahnland-bayern.de/efa"
EFA_DM_ENDPOINT = "/XML_DM_REQUEST"
EFA_SF_ENDPOINT = "/XML_STOPFINDER_REQUEST"

# DB/IRIS via marudor.de – Echtzeit für Züge am Aschaffenburg Hbf
MARUDOR_BASE_URL = "https://marudor.de/api"
MARUDOR_DEPARTURES_ENDPOINT = "/iris/v2/abfahrten"

SOURCE_EFA = "efa"
SOURCE_DB = "db"

CONF_STOP_ID = "stop_id"
CONF_STOP_NAME = "stop_name"
CONF_MAX_DEPARTURES = "max_departures"
CONF_SOURCE = "source"
CONF_LINE_FILTER = "line_filter"       # list[str] – leere Liste = alle Linien
CONF_DIRECTION_FILTER = "direction_filter"  # list[str] – leere Liste = alle Richtungen

DEFAULT_DEPARTURES = 5
UPDATE_INTERVAL = 60  # seconds
