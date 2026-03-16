"""Constants for Smart Pool Filtration Manager."""

DOMAIN = "smartpoolfiltmgr"
NAME = "Smart Pool Filtration Manager"

# Configuration keys
CONF_PUMP_SWITCH = "pump_switch"
CONF_WATER_TEMP_SENSOR = "water_temp_sensor"
CONF_SOLAR_POWER_SENSOR = "solar_power_sensor"
CONF_GRID_CONSUMPTION_SENSOR = "grid_consumption_sensor"
CONF_MIN_SOLAR_POWER = "min_solar_power"
CONF_SOLAR_PRIORITY = "solar_priority"
CONF_MIN_DAILY_DURATION = "min_daily_duration"
CONF_MAX_DAILY_DURATION = "max_daily_duration"
CONF_FILTRATION_START_HOUR = "filtration_start_hour"
CONF_FILTRATION_END_HOUR = "filtration_end_hour"
CONF_TEMP_BOOST_THRESHOLD = "temp_boost_threshold"

# Default values
DEFAULT_MIN_SOLAR_POWER = 500        # Watts minimum pour considérer la production solaire
DEFAULT_SOLAR_PRIORITY = True        # Priorité solaire activée par défaut
DEFAULT_MIN_DAILY_DURATION = 2       # Heures minimum de filtration par jour
DEFAULT_MAX_DAILY_DURATION = 12      # Heures maximum de filtration par jour
DEFAULT_FILTRATION_START_HOUR = 8    # Heure de début de plage de filtration
DEFAULT_FILTRATION_END_HOUR = 20     # Heure de fin de plage de filtration
DEFAULT_TEMP_BOOST_THRESHOLD = 28.0  # °C : au-dessus, on augmente la filtration

# Filtration duration calculation (règle T°/2 en heures)
TEMP_DURATION_TABLE = [
    (10, 1.0),
    (15, 2.0),
    (18, 3.0),
    (20, 4.0),
    (22, 5.0),
    (24, 6.0),
    (26, 7.0),
    (28, 9.0),
    (30, 12.0),
    (35, 12.0),
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

DEFAULT_WATER_HEATER_MIN_TEMP = 50.0   # °C : seuil min avant d'autoriser la pompe
DEFAULT_WATER_HEATER_HYSTERESIS = 2.0  # °C : marge anti-oscillation
# Exemple : seuil=50°C, hyst=2°C
#   ballon < 50°C        → pompe bloquée (ballon prioritaire)
#   ballon atteint 52°C  → pompe autorisée (50 + 2)
#   ballon redescend à 50°C → pompe reste autorisée (hystérésis empêche le blocage immédiat)
#   ballon < 48°C        → pompe bloquée à nouveau (50 - 2... non : on bloque en-dessous du seuil)
# En pratique : UNLOCK à (min_temp + hysteresis), RE-LOCK en-dessous de min_temp

# Pump power configuration
CONF_PUMP_POWER_W = "pump_power_w"
CONF_ROUGE_SURPLUS_MARGIN_W = "rouge_surplus_margin_w"

DEFAULT_PUMP_POWER_W = 750          # Puissance approximative de la pompe en Watts
DEFAULT_ROUGE_SURPLUS_MARGIN_W = 50 # Marge de sécurité en Watts pour éviter les micro-soutirages

# Tempo configuration keys
CONF_TEMPO_COLOR_SENSOR = "tempo_color_sensor"
CONF_TEMPO_HC_SENSOR = "tempo_hc_sensor"
CONF_TEMPO_ALLOW_BLANC_HP = "tempo_allow_blanc_hp"
CONF_TEMPO_ALLOW_ROUGE_HP = "tempo_allow_rouge_hp"
CONF_TEMPO_ALLOW_ROUGE_HC = "tempo_allow_rouge_hc"

# Tempo default values
DEFAULT_TEMPO_ALLOW_BLANC_HP = False  # Blanc HP : off sauf solaire
DEFAULT_TEMPO_ALLOW_ROUGE_HP = False  # Rouge HP : toujours off (même avec solaire, configurable)
DEFAULT_TEMPO_ALLOW_ROUGE_HC = True   # Rouge HC : autorisé (tarif HC avantageux)

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
UPDATE_INTERVAL_SECONDS = 60

# Storage key for persistence
STORAGE_KEY = f"{DOMAIN}_data"
STORAGE_VERSION = 1
