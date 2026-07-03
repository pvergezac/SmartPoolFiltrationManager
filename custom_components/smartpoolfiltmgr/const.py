"""Constants for Smart Pool Filtration Manager."""

DOMAIN = "smartpoolfiltmgr"
NAME = "Smart Pool Filtration Manager"

# Configuration keys
CONF_PUMP_SWITCH = "pump_switch"
CONF_WATER_TEMP_SENSOR = "water_temp_sensor"
CONF_SOLAR_POWER_SENSOR = "solar_power_sensor"
CONF_GRID_POWER_SENSOR = "grid_power_sensor"
CONF_MIN_SOLAR_POWER = "min_solar_power"
CONF_MIN_DAILY_DURATION = "min_daily_duration"
CONF_MAX_DAILY_DURATION = "max_daily_duration"
CONF_RESET_DAILY_HOUR = "reset_daily_hour"
CONF_SOLAR_FILTRATION_START_HOUR = "solar_filtration_start_hour"
CONF_SOLAR_FILTRATION_END_HOUR = "solar_filtration_end_hour"
CONF_GRID_FILTRATION_START_HOUR = "grid_filtration_start_hour"
CONF_GRID_FILTRATION_END_HOUR = "grid_filtration_end_hour"

# Default values
DEFAULT_MIN_SOLAR_POWER = 500  # Watts minimum pour considérer la production solaire
DEFAULT_MIN_DAILY_DURATION = 2  # Durée minimum de filtration par jour (mn)
DEFAULT_MAX_DAILY_DURATION = 24  # Durée maximum de filtration par jour (mn)
DEFAULT_RESET_DAILY_HOUR = 6  # Heure de réinitialisation durée de filtration journalière
DEFAULT_SOLAR_FILTRATION_START_HOUR = 8  # Heure de début de plage de filtration
DEFAULT_SOLAR_FILTRATION_END_HOUR = 20  # Heure de fin de plage de filtration
DEFAULT_GRID_FILTRATION_START_HOUR = 22  # Heure de début de plage de filtration complémentaire
DEFAULT_GRID_FILTRATION_END_HOUR = 6  # Heure de fin de plage de filtration complémentaire

# Filtration duration calculation (règle T°/2 en heures)
TEMP_DURATION_TABLE = [
    (10, 60.0),  # 10°C → 1h
    (15, 120.0),  # 15°C → 2h
    (18, 180.0),  # 18°C → 3h
    (20, 240.0),  # 20°C → 4h
    (22, 300.0),  # 22°C → 5h
    (24, 360.0),  # 24°C → 6h
    (26, 420.0),  # 26°C → 7h
    (28, 530.0),  # 28°C → 8h50
    (30, 1440.0),  # 30°C → 24h
    (35, 1440.0),  # 35°C → 24h
]

# Sensor & entity names
SENSOR_DAILY_RUNTIME = "pool_filtration_daily_runtime"
SENSOR_TARGET_DURATION = "pool_filtration_target_duration"
SENSOR_SOLAR_CONTRIBUTION = "pool_filtration_solar_contribution"
SENSOR_NEXT_START = "pool_filtration_next_start"
SWITCH_MANUAL_OVERRIDE = "pool_filtration_manual_override"

# Attributes
ATTR_DAILY_RUNTIME = "daily_runtime_minutes"
ATTR_TARGET_DURATION = "target_duration_minutes"
ATTR_SOLAR_RUNNING = "running_on_solar"
ATTR_LAST_START = "last_start"
ATTR_LAST_STOP = "last_stop"
ATTR_CURRENT_WATER_TEMP = "water_temperature"
ATTR_CURRENT_SOLAR_POWER = "solar_power_watts"
ATTR_MODE = "mode"

# Water heater (ballon ECS) priority configuration
CONF_WATER_HEATER_TEMP_SENSOR = "water_heater_temp_sensor"
CONF_WATER_HEATER_MIN_TEMP = "water_heater_min_temp"
CONF_WATER_HEATER_HYSTERESIS = "water_heater_hysteresis"

CONF_ACCEPTED_CONSO_BLEU = "accepted_conso_bleu"
CONF_ACCEPTED_CONSO_BLANC = "accepted_conso_blanc"
CONF_ACCEPTED_CONSO_ROUGE = "accepted_conso_rouge"

DEFAULT_ACCEPTED_CONSO_BLEU = 500.0  # W : consommation réseau
DEFAULT_ACCEPTED_CONSO_BLANC = 100.0  # W : consommation réseau
DEFAULT_ACCEPTED_CONSO_ROUGE = 50.0  # W : consommation réseau


DEFAULT_WATER_HEATER_MIN_TEMP = 40.0  # °C : seuil min avant d'autoriser la pompe
DEFAULT_WATER_HEATER_HYSTERESIS = 2.0  # °C : marge anti-oscillation
# Exemple : seuil=50°C, hyst=2°C
#   ballon < 50°C        → pompe bloquée (ballon prioritaire)
#   ballon atteint 52°C  → pompe autorisée (50 + 2)
#   ballon redescend à 50°C → pompe reste autorisée (hystérésis empêche
#     le blocage immédiat)
#   ballon < 48°C        → pompe bloquée à nouveau (50 - 2... non : on bloque
#     en-dessous du seuil)
# En pratique : UNLOCK à (min_temp + hysteresis), RE-LOCK en-dessous de min_temp

# Pump power configuration
CONF_PUMP_POWER_W = "pump_power_w"
DEFAULT_PUMP_POWER_W = 750  # Puissance approximative de la pompe
CONF_PUMP_START_POWER_THRESHOLD = "pump_start_power_threshold"
DEFAULT_PUMP_START_POWER_THRESHOLD = (
    50.0  # Consomation max pour autoriser le demarrage de la pompe (plage solaire)
)

# Tempo configuration keys
CONF_TEMPO_COLOR_SENSOR = "tempo_color_sensor"
CONF_TEMPO_HC_SENSOR = "tempo_hc_sensor"
CONF_GRID_ALLOW = "grid_allow"
CONF_GRID_ALLOW_BLEU = "grid_allow_bleu"
CONF_GRID_ALLOW_BLANC_HC = "grid_allow_blanc_hc"
CONF_GRID_ALLOW_ROUGE_HC = "grid_allow_rouge_hc"

# Tempo default values
DEFAULT_GRID_ALLOW_BLEU = True
DEFAULT_GRID_ALLOW_BLANC_HC = False
DEFAULT_GRID_ALLOW_ROUGE_HC = False

# Tempo color values (as returned by rtetempo integration)
TEMPO_COLOR_BLEU = "Bleu"
TEMPO_COLOR_BLANC = "Blanc"
TEMPO_COLOR_ROUGE = "Rouge"
TEMPO_COLOR_UNKNOWN = "Inconnu"

# Modes
MODE_AUTO = "auto"
MODE_SOLAR = "solar_only"
MODE_MANUAL = "manual"
MODE_OFF = "off"

# Update interval
UPDATE_INTERVAL_SECONDS = 300  # 5 minutes

# Storage key for persistence
STORAGE_KEY = f"{DOMAIN}_data"
STORAGE_VERSION = 1
