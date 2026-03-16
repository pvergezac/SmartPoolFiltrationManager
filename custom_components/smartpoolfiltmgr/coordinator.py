"""Data coordinator for Smart Pool Filtration Manager."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    UPDATE_INTERVAL_SECONDS,
    STORAGE_KEY,
    STORAGE_VERSION,
    TEMP_DURATION_TABLE,
    CONF_PUMP_SWITCH,
    CONF_WATER_TEMP_SENSOR,
    CONF_SOLAR_POWER_SENSOR,
    CONF_GRID_CONSUMPTION_SENSOR,
    CONF_TEMPO_COLOR_SENSOR,
    CONF_TEMPO_HC_SENSOR,
    CONF_WATER_HEATER_TEMP_SENSOR,
    CONF_MIN_SOLAR_POWER,
    CONF_SOLAR_PRIORITY,
    CONF_MIN_DAILY_DURATION,
    CONF_MAX_DAILY_DURATION,
    CONF_FILTRATION_START_HOUR,
    CONF_FILTRATION_END_HOUR,
    CONF_TEMPO_ALLOW_BLANC_HP,
    CONF_TEMPO_ALLOW_ROUGE_HP,
    CONF_TEMPO_ALLOW_ROUGE_HC,
    CONF_PUMP_POWER_W,
    CONF_ROUGE_SURPLUS_MARGIN_W,
    CONF_WATER_HEATER_MIN_TEMP,
    CONF_WATER_HEATER_HYSTERESIS,
    DEFAULT_MIN_SOLAR_POWER,
    DEFAULT_SOLAR_PRIORITY,
    DEFAULT_MIN_DAILY_DURATION,
    DEFAULT_MAX_DAILY_DURATION,
    DEFAULT_FILTRATION_START_HOUR,
    DEFAULT_FILTRATION_END_HOUR,
    DEFAULT_TEMPO_ALLOW_BLANC_HP,
    DEFAULT_TEMPO_ALLOW_ROUGE_HP,
    DEFAULT_TEMPO_ALLOW_ROUGE_HC,
    DEFAULT_PUMP_POWER_W,
    DEFAULT_ROUGE_SURPLUS_MARGIN_W,
    DEFAULT_WATER_HEATER_MIN_TEMP,
    DEFAULT_WATER_HEATER_HYSTERESIS,
    TEMPO_COLOR_BLEU,
    TEMPO_COLOR_BLANC,
    TEMPO_COLOR_ROUGE,
    TEMPO_COLOR_UNKNOWN,
    MODE_AUTO,
    MODE_SOLAR,
    MODE_MANUAL,
    MODE_OFF,
)

_LOGGER = logging.getLogger(__name__)


def calculate_target_duration(temp: float) -> float:
    """
    Calculate required filtration duration in hours based on water temperature.
    Uses the standard pool rule: T/2 hours, with min/max bounds.
    Interpolates between known points for precision.
    """
    if temp <= TEMP_DURATION_TABLE[0][0]:
        return TEMP_DURATION_TABLE[0][1]
    if temp >= TEMP_DURATION_TABLE[-1][0]:
        return TEMP_DURATION_TABLE[-1][1]

    for i in range(len(TEMP_DURATION_TABLE) - 1):
        t1, d1 = TEMP_DURATION_TABLE[i]
        t2, d2 = TEMP_DURATION_TABLE[i + 1]
        if t1 <= temp <= t2:
            ratio = (temp - t1) / (t2 - t1)
            return d1 + ratio * (d2 - d1)

    return temp / 2.0


class PoolFiltrationCoordinator(DataUpdateCoordinator):
    """Coordinator managing pool filtration logic."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        self.config_entry = config_entry
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

        # Runtime state
        self._mode: str = MODE_AUTO
        self._manual_override: bool = False
        self._pump_running: bool = False
        self._run_start: Optional[datetime] = None
        self._daily_runtime_minutes: float = 0.0
        self._last_reset_date: Optional[date] = None
        self._solar_contribution_minutes: float = 0.0
        self._hc_contribution_minutes: float = 0.0
        # Water heater hysteresis state:
        # False = ballon not yet at (min_temp + hysteresis) → pump locked
        # True  = ballon has reached unlock threshold → pump allowed until it drops below min_temp
        self._water_heater_unlocked: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def pump_running(self) -> bool:
        return self._pump_running

    @property
    def daily_runtime_minutes(self) -> float:
        return self._daily_runtime_minutes

    @property
    def solar_contribution_minutes(self) -> float:
        return self._solar_contribution_minutes

    @property
    def hc_contribution_minutes(self) -> float:
        return self._hc_contribution_minutes

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _get_option(self, key, default):
        return self.config_entry.options.get(key, default)

    @property
    def min_solar_power(self) -> float:
        return float(self._get_option(CONF_MIN_SOLAR_POWER, DEFAULT_MIN_SOLAR_POWER))

    @property
    def solar_priority(self) -> bool:
        return bool(self._get_option(CONF_SOLAR_PRIORITY, DEFAULT_SOLAR_PRIORITY))

    @property
    def min_daily_duration_hours(self) -> float:
        return float(self._get_option(CONF_MIN_DAILY_DURATION, DEFAULT_MIN_DAILY_DURATION))

    @property
    def max_daily_duration_hours(self) -> float:
        return float(self._get_option(CONF_MAX_DAILY_DURATION, DEFAULT_MAX_DAILY_DURATION))

    @property
    def filtration_start_hour(self) -> int:
        return int(self._get_option(CONF_FILTRATION_START_HOUR, DEFAULT_FILTRATION_START_HOUR))

    @property
    def filtration_end_hour(self) -> int:
        return int(self._get_option(CONF_FILTRATION_END_HOUR, DEFAULT_FILTRATION_END_HOUR))

    @property
    def tempo_allow_blanc_hp(self) -> bool:
        return bool(self._get_option(CONF_TEMPO_ALLOW_BLANC_HP, DEFAULT_TEMPO_ALLOW_BLANC_HP))

    @property
    def tempo_allow_rouge_hc(self) -> bool:
        return bool(self._get_option(CONF_TEMPO_ALLOW_ROUGE_HC, DEFAULT_TEMPO_ALLOW_ROUGE_HC))

    @property
    def tempo_allow_rouge_hp(self) -> bool:
        return bool(self._get_option(CONF_TEMPO_ALLOW_ROUGE_HP, DEFAULT_TEMPO_ALLOW_ROUGE_HP))

    @property
    def pump_power_w(self) -> float:
        return float(self._get_option(CONF_PUMP_POWER_W, DEFAULT_PUMP_POWER_W))

    @property
    def rouge_surplus_margin_w(self) -> float:
        """Safety margin in Watts to avoid micro grid draws due to measurement lag."""
        return float(self._get_option(CONF_ROUGE_SURPLUS_MARGIN_W, DEFAULT_ROUGE_SURPLUS_MARGIN_W))

    @property
    def water_heater_min_temp(self) -> float:
        """Minimum water heater temperature before allowing pool pump to run."""
        return float(self._get_option(CONF_WATER_HEATER_MIN_TEMP, DEFAULT_WATER_HEATER_MIN_TEMP))

    @property
    def water_heater_hysteresis(self) -> float:
        """Hysteresis in °C above min_temp required to unlock the pump."""
        return float(self._get_option(CONF_WATER_HEATER_HYSTERESIS, DEFAULT_WATER_HEATER_HYSTERESIS))

    # ------------------------------------------------------------------
    # Sensor reading helpers
    # ------------------------------------------------------------------

    def _get_sensor_float(self, entity_id: str) -> Optional[float]:
        """Safely read a numeric sensor value."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", None):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _get_sensor_str(self, entity_id: str) -> Optional[str]:
        """Safely read a string sensor value."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return state.state

    def get_water_temperature(self) -> Optional[float]:
        entity_id = self.config_entry.data.get(CONF_WATER_TEMP_SENSOR)
        return self._get_sensor_float(entity_id) if entity_id else None

    def get_solar_power(self) -> Optional[float]:
        entity_id = self.config_entry.data.get(CONF_SOLAR_POWER_SENSOR)
        return self._get_sensor_float(entity_id) if entity_id else None

    def get_grid_consumption(self) -> Optional[float]:
        entity_id = self.config_entry.data.get(CONF_GRID_CONSUMPTION_SENSOR)
        return self._get_sensor_float(entity_id) if entity_id else None

    def get_solar_surplus_for_pump(self) -> Optional[float]:
        """
        Calculate the solar surplus available to run the pump without drawing from the grid.

        Uses the net grid meter (positive = import, negative = export) combined with
        solar production to derive current household consumption, then computes how
        much solar headroom remains after the house load.

        Formula:
            house_load   = solar_production - grid_net
                           (grid_net negative when exporting → house_load < solar)
            surplus      = solar_production - house_load
                         = grid_net  (when grid_net < 0: surplus = |export|)

        In practice:
            - grid_net = -800W (exporting 800W) → surplus = 800W available for pump
            - grid_net = +200W (importing 200W)  → surplus = -200W (deficit, can't add pump)
            - grid_net =  0W  (balanced)          → surplus = 0W (just enough for house)

        Returns None if either sensor is unavailable.
        """
        solar = self.get_solar_power()
        grid_net = self.get_grid_consumption()

        if solar is None or grid_net is None:
            return None

        # surplus = what the grid would absorb if we turned the pump on
        # = current export (negative grid) minus nothing, or current import flipped
        # Simply: surplus = -grid_net when exporting, negative when importing
        return -grid_net  # positive = surplus available, negative = already importing

    def get_tempo_color(self) -> Optional[str]:
        """
        Return current Tempo color: 'Bleu', 'Blanc', 'Rouge', or None if not configured.
        Compatible with hekmon/rtetempo (sensor.rte_tempo_couleur_actuelle).
        """
        entity_id = self.config_entry.data.get(CONF_TEMPO_COLOR_SENSOR)
        return self._get_sensor_str(entity_id) if entity_id else None

    def get_tempo_is_hc(self) -> Optional[bool]:
        """
        Return True if currently in Heures Creuses, False if HP, None if not configured.
        Compatible with hekmon/rtetempo (binary_sensor.rte_tempo_heures_creuses).
        HC = 22h00 -> 06h00.
        """
        entity_id = self.config_entry.data.get(CONF_TEMPO_HC_SENSOR)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return state.state == "on"

    def get_water_heater_temperature(self) -> Optional[float]:
        """Return current water heater (ballon ECS) temperature, or None if not configured."""
        entity_id = self.config_entry.data.get(CONF_WATER_HEATER_TEMP_SENSOR)
        return self._get_sensor_float(entity_id) if entity_id else None

    def _check_water_heater_priority(self) -> tuple[bool, str]:
        """
        Evaluate whether the water heater (ballon ECS) blocks the pool pump.

        Uses a two-threshold hysteresis to avoid pump oscillation near the setpoint:

            LOCK threshold   = water_heater_min_temp
            UNLOCK threshold = water_heater_min_temp + water_heater_hysteresis

        State machine:
            _water_heater_unlocked == False:
                → pump stays blocked until temp >= UNLOCK threshold
                → once reached, set _water_heater_unlocked = True

            _water_heater_unlocked == True:
                → pump is allowed
                → if temp drops below LOCK threshold, set _water_heater_unlocked = False

        This prevents rapid on/off cycling when the ballon is exactly at the threshold.

        Example with min=50°C, hyst=2°C:
            Ballon at 48°C → locked (unlocked=False, needs 52°C to unlock)
            Ballon rises to 52°C → unlocked (unlocked=True)
            Ballon cools to 51°C → still unlocked (above 50°C lock threshold)
            Ballon cools to 49°C → locked again (unlocked=False)

        Returns (pump_allowed: bool, reason: str).
        If water heater sensor not configured, always returns (True, "no_water_heater").
        """
        temp = self.get_water_heater_temperature()

        if temp is None:
            # Sensor not configured or unavailable → no restriction
            # Unavailability is logged but does not block (fail-open for pool health)
            entity_id = self.config_entry.data.get(CONF_WATER_HEATER_TEMP_SENSOR)
            if entity_id:
                _LOGGER.debug("Water heater sensor unavailable, ignoring priority check")
            return True, "no_water_heater"

        lock_threshold = self.water_heater_min_temp
        unlock_threshold = lock_threshold + self.water_heater_hysteresis

        if not self._water_heater_unlocked:
            # Currently locked — check if we've reached the unlock threshold
            if temp >= unlock_threshold:
                self._water_heater_unlocked = True
                _LOGGER.info(
                    "Water heater reached %.1f°C (unlock threshold %.1f°C) — pump unlocked",
                    temp, unlock_threshold,
                )
                return True, f"water_heater_unlocked_{temp:.1f}c"
            else:
                return False, f"water_heater_priority_{temp:.1f}c_need_{unlock_threshold:.1f}c"
        else:
            # Currently unlocked — check if temp dropped below lock threshold
            if temp < lock_threshold:
                self._water_heater_unlocked = False
                _LOGGER.info(
                    "Water heater dropped to %.1f°C (below %.1f°C) — pump locked for heater priority",
                    temp, lock_threshold,
                )
                return False, f"water_heater_relocked_{temp:.1f}c"
            else:
                return True, f"water_heater_ok_{temp:.1f}c"

    def get_target_duration_hours(self) -> float:
        """Calculate today's target filtration duration in hours."""
        temp = self.get_water_temperature()
        if temp is None:
            return self.min_daily_duration_hours

        calculated = calculate_target_duration(temp)
        return max(self.min_daily_duration_hours,
                   min(self.max_daily_duration_hours, calculated))

    # ------------------------------------------------------------------
    # Tempo decision helper
    # ------------------------------------------------------------------

    def _tempo_allows_grid_run(self, solar_available: bool) -> tuple[bool, str]:
        """
        Evaluate whether Tempo contract allows running the pump on grid power.

        For ROUGE days, applies strict surplus-based logic:
        the pump is only allowed if the solar surplus strictly covers the pump
        power + safety margin, ensuring zero grid draw regardless of house load.

        For BLANC and BLEU, standard solar_available flag is sufficient.

        Decision matrix:
        Bleu  + *   + *                              -> OK (tarif le moins cher)
        Blanc + HC  + *                              -> OK (tarif HC acceptable)
        Blanc + HP  + surplus >= pump+margin         -> OK (energie solaire)
        Blanc + HP  + deficit                        -> configurable (defaut OFF)
        Rouge + HC  + *                              -> configurable (defaut ON)
        Rouge + HP  + surplus >= pump+margin         -> OK strictement sur surplus
        Rouge + HP  + deficit ou surplus insuffisant -> BLOQUE (zero soutirage reseau)
        """
        tempo_color = self.get_tempo_color()
        is_hc = self.get_tempo_is_hc()

        # Tempo not configured -> no restriction
        if tempo_color is None:
            return True, "no_tempo"

        # ------------------------------------------------------------------
        # Jour ROUGE : logique stricte de surplus — aucun soutirage réseau
        # ------------------------------------------------------------------
        if tempo_color == TEMPO_COLOR_ROUGE:
            if is_hc:
                # Heures creuses Rouge : tarif HC seulement, configurable
                if self.tempo_allow_rouge_hc:
                    return True, "rouge_hc_allowed"
                return False, "rouge_hc_blocked"

            # Heures pleines Rouge : on vérifie le surplus réel
            surplus = self.get_solar_surplus_for_pump()

            if surplus is None:
                # Capteurs indisponibles → prudence maximale, on bloque
                _LOGGER.warning(
                    "Rouge HP: grid/solar sensors unavailable, blocking pump to avoid grid draw"
                )
                return False, "rouge_hp_no_sensor"

            required = self.pump_power_w + self.rouge_surplus_margin_w
            if surplus >= required:
                return True, f"rouge_hp_surplus_ok_{surplus:.0f}W"

            return False, f"rouge_hp_surplus_insufficient_{surplus:.0f}W_need_{required:.0f}W"

        # ------------------------------------------------------------------
        # Jour BLANC
        # ------------------------------------------------------------------
        if tempo_color == TEMPO_COLOR_BLANC:
            if is_hc:
                return True, "blanc_hc"
            # HP : le surplus solaire simple suffit (pas besoin du calcul précis)
            if solar_available:
                return True, "blanc_hp_solar"
            if self.tempo_allow_blanc_hp:
                return True, "blanc_hp_allowed"
            return False, "blanc_hp_blocked"

        # ------------------------------------------------------------------
        # Jour BLEU : toujours autorisé
        # ------------------------------------------------------------------
        if tempo_color == TEMPO_COLOR_BLEU:
            return True, "bleu_grid"

        # Couleur inconnue -> prudence
        _LOGGER.warning("Unknown Tempo color '%s', blocking grid run", tempo_color)
        return False, f"unknown_color_{tempo_color}"

    # ------------------------------------------------------------------
    # Core decision logic
    # ------------------------------------------------------------------

    def _should_pump_run(self) -> tuple[bool, str]:
        """
        Main decision: should the pump run right now?

        Returns (should_run: bool, reason: str) for logging and diagnostics.

        Priority order:
        1. Manual override -> respect it
        2. Mode OFF -> never run
        3. Max daily duration reached -> stop
        4. Outside allowed hours -> stop
        5. MODE_SOLAR -> only run on solar surplus
        6. MODE_AUTO -> solar first, then Tempo-aware grid fallback
        """
        now = dt_util.now()

        # 1. Manual override
        if self._mode == MODE_MANUAL:
            return self._manual_override, "manual"

        # 2. Mode OFF
        if self._mode == MODE_OFF:
            return False, "mode_off"

        # 3. Max daily duration reached
        target_hours = self.get_target_duration_hours()
        target_minutes = target_hours * 60
        if self._daily_runtime_minutes >= target_minutes:
            return False, "quota_reached"

        # 4. Outside allowed time window
        current_hour = now.hour + now.minute / 60.0
        if not (self.filtration_start_hour <= current_hour < self.filtration_end_hour):
            return False, "outside_hours"

        # 5. Water heater (ballon ECS) priority — checked before solar/Tempo
        #    The ballon must be sufficiently hot before we can claim solar surplus for the pool.
        #    This applies in all automatic modes: even if solar is available, if the ballon
        #    is still cold the MSunPV router will be using that surplus to heat water.
        #    Manual mode bypasses this check (operator takes responsibility).
        wh_ok, wh_reason = self._check_water_heater_priority()
        if not wh_ok:
            return False, wh_reason

        solar_power = self.get_solar_power()
        solar_available = solar_power is not None and solar_power >= self.min_solar_power

        # 6. Solar-only mode
        if self._mode == MODE_SOLAR:
            if solar_available:
                return True, "solar_only_mode_solar"
            return False, "solar_only_mode_no_solar"

        # 7. Auto mode
        if self._mode == MODE_AUTO:

            # 7a. Solaire dispo -> toujours ON (ballon déjà prioritaire vérifié ci-dessus)
            if solar_available:
                return True, "auto_solar"

            # 7b. Verifier si Tempo autorise le reseau
            tempo_ok, tempo_reason = self._tempo_allows_grid_run(solar_available=False)
            if not tempo_ok:
                return False, f"tempo_blocked_{tempo_reason}"

            # 7c. Tempo OK -> logique de completion
            remaining_minutes = target_minutes - self._daily_runtime_minutes
            remaining_window_hours = self.filtration_end_hour - current_hour
            estimated_solar_minutes = remaining_window_hours * 60 * 0.4
            if remaining_minutes > estimated_solar_minutes:
                return True, f"auto_grid_{tempo_reason}"

            return False, "auto_waiting_for_solar"

        return False, "unknown_mode"

    # ------------------------------------------------------------------
    # Pump control
    # ------------------------------------------------------------------

    async def _set_pump(self, state: bool) -> None:
        """Turn the pump switch on or off."""
        pump_entity = self.config_entry.data.get(CONF_PUMP_SWITCH)
        if not pump_entity:
            return

        service = "turn_on" if state else "turn_off"
        await self.hass.services.async_call(
            "switch",
            service,
            {"entity_id": pump_entity},
            blocking=True,
        )
        _LOGGER.info("Pump %s via pool_filtration controller", "started" if state else "stopped")

    # ------------------------------------------------------------------
    # Daily reset
    # ------------------------------------------------------------------

    def _check_daily_reset(self) -> None:
        """Reset daily counters at midnight."""
        today = dt_util.now().date()
        if self._last_reset_date != today:
            _LOGGER.info("Daily reset: new filtration day %s", today)
            self._daily_runtime_minutes = 0.0
            self._solar_contribution_minutes = 0.0
            self._hc_contribution_minutes = 0.0
            self._last_reset_date = today

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Main update loop called every UPDATE_INTERVAL_SECONDS."""
        self._check_daily_reset()

        now = dt_util.now()
        solar_power = self.get_solar_power()
        water_temp = self.get_water_temperature()
        grid_consumption = self.get_grid_consumption()
        tempo_color = self.get_tempo_color()
        tempo_is_hc = self.get_tempo_is_hc()
        target_hours = self.get_target_duration_hours()
        solar_surplus = self.get_solar_surplus_for_pump()
        water_heater_temp = self.get_water_heater_temperature()

        solar_available = solar_power is not None and solar_power >= self.min_solar_power
        should_run, reason = self._should_pump_run()

        # Accumulate runtime if pump was running
        if self._pump_running and self._run_start is not None:
            elapsed = (now - self._run_start).total_seconds() / 60.0
            self._daily_runtime_minutes += elapsed

            if solar_available:
                self._solar_contribution_minutes += elapsed
            elif tempo_is_hc:
                self._hc_contribution_minutes += elapsed

            self._run_start = now  # reset for next interval

        # Act on decision
        if should_run and not self._pump_running:
            await self._set_pump(True)
            self._pump_running = True
            self._run_start = now
            _LOGGER.info(
                "Pump ON [%s] -- pool=%.1fC ballon=%.1fC solar=%.0fW surplus=%.0fW tempo=%s %s runtime=%.0f/%.0f min",
                reason,
                water_temp or 0,
                water_heater_temp or 0,
                solar_power or 0,
                solar_surplus or 0,
                tempo_color or "N/A",
                "HC" if tempo_is_hc else "HP",
                self._daily_runtime_minutes,
                target_hours * 60,
            )

        elif not should_run and self._pump_running:
            await self._set_pump(False)
            self._pump_running = False
            self._run_start = None
            _LOGGER.info(
                "Pump OFF [%s] -- ballon=%.1fC surplus=%.0fW runtime=%.0f/%.0f min tempo=%s %s",
                reason,
                water_heater_temp or 0,
                solar_surplus or 0,
                self._daily_runtime_minutes,
                target_hours * 60,
                tempo_color or "N/A",
                "HC" if tempo_is_hc else "HP",
            )

        await self._save_state()

        # Compute water heater status for sensors
        wh_configured = self.config_entry.data.get(CONF_WATER_HEATER_TEMP_SENSOR) is not None
        wh_unlock_threshold = self.water_heater_min_temp + self.water_heater_hysteresis

        return {
            "pump_running": self._pump_running,
            "mode": self._mode,
            "decision_reason": reason,
            "water_temp": water_temp,
            "solar_power": solar_power,
            "solar_available": solar_available,
            "grid_consumption": grid_consumption,
            "solar_surplus_w": solar_surplus,
            "pump_power_w": self.pump_power_w,
            "rouge_surplus_margin_w": self.rouge_surplus_margin_w,
            "tempo_color": tempo_color or TEMPO_COLOR_UNKNOWN,
            "tempo_is_hc": tempo_is_hc,
            "tempo_configured": tempo_color is not None,
            "water_heater_temp": water_heater_temp,
            "water_heater_configured": wh_configured,
            "water_heater_unlocked": self._water_heater_unlocked,
            "water_heater_min_temp": self.water_heater_min_temp,
            "water_heater_unlock_threshold": wh_unlock_threshold,
            "daily_runtime_minutes": self._daily_runtime_minutes,
            "target_duration_minutes": target_hours * 60,
            "solar_contribution_minutes": self._solar_contribution_minutes,
            "hc_contribution_minutes": self._hc_contribution_minutes,
            "last_reset_date": str(self._last_reset_date),
        }

    # ------------------------------------------------------------------
    # Mode setters
    # ------------------------------------------------------------------

    async def set_mode(self, mode: str) -> None:
        """Change operating mode."""
        if mode not in (MODE_AUTO, MODE_SOLAR, MODE_MANUAL, MODE_OFF):
            raise ValueError(f"Unknown mode: {mode}")
        self._mode = mode
        _LOGGER.info("Pool filtration mode changed to: %s", mode)
        await self.async_refresh()

    async def set_manual_override(self, state: bool) -> None:
        """Set manual pump state (only effective in MANUAL mode)."""
        self._manual_override = state
        if self._mode != MODE_MANUAL:
            self._mode = MODE_MANUAL
        await self.async_refresh()

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    async def _save_state(self) -> None:
        """Persist runtime data across HA restarts."""
        await self._store.async_save({
            "daily_runtime_minutes": self._daily_runtime_minutes,
            "solar_contribution_minutes": self._solar_contribution_minutes,
            "hc_contribution_minutes": self._hc_contribution_minutes,
            "last_reset_date": str(self._last_reset_date),
            "mode": self._mode,
        })

    async def async_load_state(self) -> None:
        """Load persisted state on startup."""
        stored = await self._store.async_load()
        if stored:
            today = dt_util.now().date()
            stored_date_str = stored.get("last_reset_date")
            try:
                stored_date = date.fromisoformat(stored_date_str) if stored_date_str else None
            except (ValueError, TypeError):
                stored_date = None

            if stored_date == today:
                self._daily_runtime_minutes = stored.get("daily_runtime_minutes", 0.0)
                self._solar_contribution_minutes = stored.get("solar_contribution_minutes", 0.0)
                self._hc_contribution_minutes = stored.get("hc_contribution_minutes", 0.0)
                _LOGGER.info(
                    "Restored today's runtime: %.0f min (solar: %.0f min, HC: %.0f min)",
                    self._daily_runtime_minutes,
                    self._solar_contribution_minutes,
                    self._hc_contribution_minutes,
                )
            else:
                _LOGGER.info("New day detected -- resetting daily counters")

            self._mode = stored.get("mode", MODE_AUTO)
            self._last_reset_date = today
