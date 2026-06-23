"""Constants for the Kinoheld integration."""

DOMAIN = "kinoheld"
PLATFORMS = ["sensor"]

# Config entry keys
CONF_CINEMA_ID = "cinema_id"
CONF_CINEMA_NAME = "cinema_name"
CONF_CINEMA_CITY = "cinema_city"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # minutes
DEFAULT_MOVIE_COUNT = 10

# Coordinator update key
UPDATE_COORDINATOR = "coordinator"

# Attribute names
ATTR_MOVIES = "movies"
ATTR_MOVIE_COUNT = "movie_count"
ATTR_CINEMA_NAME = "cinema_name"
ATTR_CINEMA_ID = "cinema_id"
ATTR_LAST_UPDATED = "last_updated"
