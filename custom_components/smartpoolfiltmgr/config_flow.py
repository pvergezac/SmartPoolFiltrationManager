"""Config flow for Smart Pool Filtration Manager."""

from __future__ import annotations

from typing import Any, Self

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch.const import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    CONF_ACCEPTED_CONSO_BLANC,
    CONF_ACCEPTED_CONSO_BLEU,
    CONF_ACCEPTED_CONSO_ROUGE,
    CONF_GRID_ALLOW,
    CONF_GRID_ALLOW_BLANC_HC,
    CONF_GRID_ALLOW_BLEU,
    CONF_GRID_ALLOW_ROUGE_HC,
    CONF_GRID_FILTRATION_END_HOUR,
    CONF_GRID_FILTRATION_START_HOUR,
    CONF_GRID_POWER_SENSOR,
    CONF_MAX_DAILY_DURATION,
    CONF_MIN_DAILY_DURATION,
    CONF_MIN_SOLAR_POWER,
    CONF_PUMP_START_POWER_THRESHOLD,
    CONF_PUMP_SWITCH,
    CONF_RESET_DAILY_HOUR,
    CONF_SOLAR_FILTRATION_END_HOUR,
    CONF_SOLAR_FILTRATION_START_HOUR,
    CONF_SOLAR_POWER_SENSOR,
    CONF_TEMPO_COLOR_SENSOR,
    CONF_TEMPO_HC_SENSOR,
    CONF_WATER_HEATER_HYSTERESIS,
    CONF_WATER_HEATER_MIN_TEMP,
    CONF_WATER_HEATER_TEMP_SENSOR,
    CONF_WATER_TEMP_SENSOR,
    DEFAULT_ACCEPTED_CONSO_BLANC,
    DEFAULT_ACCEPTED_CONSO_BLEU,
    DEFAULT_ACCEPTED_CONSO_ROUGE,
    DEFAULT_GRID_ALLOW_BLANC_HC,
    DEFAULT_GRID_ALLOW_BLEU,
    DEFAULT_GRID_ALLOW_ROUGE_HC,
    DEFAULT_GRID_FILTRATION_END_HOUR,
    DEFAULT_GRID_FILTRATION_START_HOUR,
    DEFAULT_MAX_DAILY_DURATION,
    DEFAULT_MIN_DAILY_DURATION,
    DEFAULT_MIN_SOLAR_POWER,
    DEFAULT_PUMP_START_POWER_THRESHOLD,
    DEFAULT_RESET_DAILY_HOUR,
    DEFAULT_SOLAR_FILTRATION_END_HOUR,
    DEFAULT_SOLAR_FILTRATION_START_HOUR,
    DEFAULT_WATER_HEATER_HYSTERESIS,
    DEFAULT_WATER_HEATER_MIN_TEMP,
    DOMAIN,
)


class PoolFiltrationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Pool Filtration Manager."""

    VERSION = 1

    def is_matching(self, other_flow: Self) -> bool:
        """Return True if other_flow is matching this flow."""
        raise NotImplementedError

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}

        if user_input is not None:
            errors = await self._validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title="Smart Pool Filtration Manager",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_PUMP_SWITCH): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN])
                ),
                vol.Required(CONF_WATER_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],  # , INPUT_NUMBER_DOMAIN],
                        device_class="temperature",
                    )
                ),
                vol.Required(CONF_SOLAR_POWER_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],  # , INPUT_NUMBER_DOMAIN],
                        device_class="power",
                    )
                ),
                vol.Optional(CONF_GRID_POWER_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],  # , INPUT_NUMBER_DOMAIN],
                        device_class="power",
                    )
                ),
                # Tempo RTE — optionnel mais recommandé
                vol.Optional(CONF_TEMPO_COLOR_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN])
                ),
                vol.Optional(CONF_TEMPO_HC_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=[BINARY_SENSOR_DOMAIN])
                ),
                # Ballon ECS (MSunPV) — optionnel, priorité sur la pompe
                vol.Optional(CONF_WATER_HEATER_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],  # , INPUT_NUMBER_DOMAIN],
                        device_class="temperature",
                    )
                ),
            }
        )
        self.add_suggested_values_to_schema

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        # HA >= 2024.x : OptionsFlow.config_entry est une propriété en lecture seule
        # fournie automatiquement par HA — ne pas passer config_entry au constructeur.
        return SmartPoolFiltrationManagerOptionsFlow()

    async def _validate_input(self, hass: HomeAssistant, data: dict) -> dict:
        """Validate that required entities exist in HA."""
        errors = {}
        for key in [CONF_PUMP_SWITCH, CONF_WATER_TEMP_SENSOR, CONF_SOLAR_POWER_SENSOR]:
            if key in data and not hass.states.get(data[key]):
                errors[key] = "entity_not_found"
        return errors


class SmartPoolFiltrationManagerOptionsFlow(config_entries.OptionsFlow):
    """Options flow — no __init__ needed, HA injects config_entry automatically."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        schema = vol.Schema(
            {
                # --- Filtration ---
                vol.Required(
                    CONF_RESET_DAILY_HOUR,
                    default=options.get(CONF_RESET_DAILY_HOUR, DEFAULT_RESET_DAILY_HOUR),
                    description="doit correspondre avec la fin des heures creuses de nuit",
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                vol.Required(
                    CONF_MIN_DAILY_DURATION,
                    default=options.get(CONF_MIN_DAILY_DURATION, DEFAULT_MIN_DAILY_DURATION),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=4,
                        step=0.5,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                vol.Required(
                    CONF_MAX_DAILY_DURATION,
                    default=options.get(CONF_MAX_DAILY_DURATION, DEFAULT_MAX_DAILY_DURATION),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=2,
                        max=24,
                        step=0.5,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                # -----------------------------------------
                vol.Required(
                    CONF_SOLAR_FILTRATION_START_HOUR,
                    default=options.get(
                        CONF_SOLAR_FILTRATION_START_HOUR, DEFAULT_SOLAR_FILTRATION_START_HOUR
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                vol.Required(
                    CONF_SOLAR_FILTRATION_END_HOUR,
                    default=options.get(
                        CONF_SOLAR_FILTRATION_END_HOUR, DEFAULT_SOLAR_FILTRATION_END_HOUR
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                vol.Optional(
                    CONF_MIN_SOLAR_POWER,
                    default=options.get(CONF_MIN_SOLAR_POWER, DEFAULT_MIN_SOLAR_POWER),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100,
                        max=5000,
                        step=50,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.SLIDER,  #  "slider",
                    )
                ),
                # --- Priorité ballon ECS (MSunPV) ---
                vol.Optional(
                    CONF_WATER_HEATER_MIN_TEMP,
                    default=options.get(CONF_WATER_HEATER_MIN_TEMP, DEFAULT_WATER_HEATER_MIN_TEMP),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=30,
                        max=75,
                        step=1,
                        unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                vol.Optional(
                    CONF_WATER_HEATER_HYSTERESIS,
                    default=options.get(
                        CONF_WATER_HEATER_HYSTERESIS, DEFAULT_WATER_HEATER_HYSTERESIS
                    ),
                ): cv.positive_float,
                vol.Optional(
                    CONF_PUMP_START_POWER_THRESHOLD,
                    default=options.get(
                        CONF_PUMP_START_POWER_THRESHOLD, DEFAULT_PUMP_START_POWER_THRESHOLD
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-2000,
                        max=2000,
                        step=100,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider",
                    )
                ),
                # -----------------------------------------
                vol.Optional(
                    CONF_ACCEPTED_CONSO_BLEU,
                    default=options.get(CONF_ACCEPTED_CONSO_BLEU, DEFAULT_ACCEPTED_CONSO_BLEU),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=4000,
                        step=100,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider",
                    )
                ),
                vol.Optional(
                    CONF_ACCEPTED_CONSO_BLANC,
                    default=options.get(CONF_ACCEPTED_CONSO_BLANC, DEFAULT_ACCEPTED_CONSO_BLANC),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=4000,
                        step=100,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider",
                    )
                ),
                vol.Optional(
                    CONF_ACCEPTED_CONSO_ROUGE,
                    default=options.get(CONF_ACCEPTED_CONSO_ROUGE, DEFAULT_ACCEPTED_CONSO_ROUGE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=4000,
                        step=100,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider",
                    )
                ),
                # *****************************************
                vol.Optional(
                    CONF_GRID_FILTRATION_START_HOUR,
                    default=options.get(
                        CONF_GRID_FILTRATION_START_HOUR, DEFAULT_GRID_FILTRATION_START_HOUR
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                vol.Optional(
                    CONF_GRID_FILTRATION_END_HOUR,
                    default=options.get(
                        CONF_GRID_FILTRATION_END_HOUR, DEFAULT_GRID_FILTRATION_END_HOUR
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,  # "slider"
                    )
                ),
                # -----------------------------------------
                # --- Tempo ---
                vol.Optional(
                    CONF_GRID_ALLOW,
                    default=options.get(CONF_GRID_ALLOW, DEFAULT_GRID_ALLOW_BLEU),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_GRID_ALLOW_BLEU,
                    default=options.get(CONF_GRID_ALLOW_BLEU, DEFAULT_GRID_ALLOW_BLEU),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_GRID_ALLOW_BLANC_HC,
                    default=options.get(CONF_GRID_ALLOW_BLANC_HC, DEFAULT_GRID_ALLOW_BLANC_HC),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_GRID_ALLOW_ROUGE_HC,
                    default=options.get(CONF_GRID_ALLOW_ROUGE_HC, DEFAULT_GRID_ALLOW_ROUGE_HC),
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
