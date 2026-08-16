DOMAIN = "vab"
USER_AGENT = "ha-vab-integration/2.0 (https://github.com/mxkissnr/ha-vab-integration)"

EFA_BASE_URL = "https://bahnland-bayern.de/efa"
EFA_DM_ENDPOINT = "/XML_DM_REQUEST"
EFA_SF_ENDPOINT = "/XML_STOPFINDER_REQUEST"

CONF_STOP_ID = "stop_id"
CONF_STOP_NAME = "stop_name"
CONF_MAX_DEPARTURES = "max_departures"
CONF_LINE_FILTER = "line_filter"
CONF_DIRECTION_FILTER = "direction_filter"
CONF_WALK_TIME = "walk_time"

DEFAULT_DEPARTURES = 5
UPDATE_INTERVAL = 60  # seconds

DEFAULT_LEAVE_THRESHOLD = 2  # minutes

SERVICE_WATCH_DEPARTURE = "watch_departure"
SERVICE_UNWATCH_DEPARTURE = "unwatch_departure"
