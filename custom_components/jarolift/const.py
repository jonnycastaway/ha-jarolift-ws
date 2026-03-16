DOMAIN = "jarolift"

CONF_HOST = "host"
CONF_NUM_CHANNELS = "num_channels"
CONF_NUM_GROUPS = "num_groups"
CONF_CHANNEL_NAMES = "channel_names"
CONF_GROUP_NAMES = "group_names"

DEFAULT_NUM_CHANNELS = 4
DEFAULT_NUM_GROUPS = 0
DEFAULT_PORT = 80

WS_RECONNECT_INTERVAL = 10  # seconds

# WebSocket message types
WS_TYPE_SEND_DATA = "sendData"
WS_TYPE_UPDATE_JSON = "updateJSON"
WS_TYPE_HEARTBEAT = "heartbeat"

# Element ID prefixes
ELEMENT_CHANNEL = "p01"
ELEMENT_GROUP = "p02"

# Actions
ACTION_UP = "up"
ACTION_DOWN = "down"
ACTION_STOP = "stop"
ACTION_SHADE = "shade"
