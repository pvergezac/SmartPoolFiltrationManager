"""Sensors for Smart Pool Filtration Manager."""
from __future__ import annotations

from typing import Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolFiltrationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolFiltrationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PoolDailyRuntimeSensor(coordinator, entry),
        PoolTargetDurationSensor(coordinator, entry),
        PoolSolarContributionSensor(coordinator, entry),
        PoolModeSensor(coordinator, entry),
        PoolTempoSensor(coordinator, entry),
        PoolWaterHeaterSensor(coordinator, entry),
    ])


class PoolBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for pool filtration sensors."""

    def __init__(self, coordinator: PoolFiltrationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart Pool Filtration Manager",
            "manufacturer": "Custom",
            "model": "Pool Filtration v1.0",
        }


class PoolDailyRuntimeSensor(PoolBaseSensor):
    """Minutes of filtration done today."""

    _attr_name = "Pool Filtration — Durée journalière"
    _attr_icon = "mdi:timer"
    _attr_native_unit_of_measurement = "min"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 0

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_daily_runtime"

    @property
    def native_value(self):
        if self.coordinator.data:
            return round(self.coordinator.data.get("daily_runtime_minutes", 0), 1)
        return 0

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "target_minutes": round(data.get("target_duration_minutes", 0), 1),
            "progress_pct": round(
                min(100, data.get("daily_runtime_minutes", 0) /
                    max(1, data.get("target_duration_minutes", 1)) * 100), 1
            ),
            "solar_contribution_minutes": round(data.get("solar_contribution_minutes", 0), 1),
            "hc_contribution_minutes": round(data.get("hc_contribution_minutes", 0), 1),
            "decision_reason": data.get("decision_reason", ""),
        }


class PoolTargetDurationSensor(PoolBaseSensor):
    """Target filtration duration calculated from water temperature."""

    _attr_name = "Pool Filtration — Durée cible"
    _attr_icon = "mdi:target"
    _attr_native_unit_of_measurement = "min"
    _attr_suggested_display_precision = 0

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_target_duration"

    @property
    def native_value(self):
        if self.coordinator.data:
            return round(self.coordinator.data.get("target_duration_minutes", 0), 1)
        return 0

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        temp = data.get("water_temp")
        return {
            "water_temperature_c": temp,
            "calculation_method": "T/2 rule (interpolated)",
        }


class PoolSolarContributionSensor(PoolBaseSensor):
    """Solar energy contribution to filtration today."""

    _attr_name = "Pool Filtration — Contribution solaire"
    _attr_icon = "mdi:solar-power"
    _attr_native_unit_of_measurement = "min"
    _attr_suggested_display_precision = 0

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_solar_contribution"

    @property
    def native_value(self):
        if self.coordinator.data:
            return round(self.coordinator.data.get("solar_contribution_minutes", 0), 1)
        return 0

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        runtime = data.get("daily_runtime_minutes", 0)
        solar = data.get("solar_contribution_minutes", 0)
        return {
            "solar_percentage": round(solar / max(1, runtime) * 100, 1) if runtime > 0 else 0,
            "current_solar_power_w": data.get("solar_power"),
            "running_on_solar": data.get("solar_running", False),
        }


class PoolModeSensor(PoolBaseSensor):
    """Current operating mode."""

    _attr_name = "Pool Filtration — Mode"
    _attr_icon = "mdi:pool"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_mode"

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data.get("mode", "unknown")
        return "unknown"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "pump_running": data.get("pump_running", False),
            "water_temp_c": data.get("water_temp"),
            "solar_power_w": data.get("solar_power"),
            "grid_consumption_w": data.get("grid_consumption"),
        }


class PoolTempoSensor(PoolBaseSensor):
    """Tempo contract status and its effect on filtration decisions."""

    _attr_name = "Pool Filtration — Tempo"
    _attr_icon = "mdi:lightning-bolt-circle"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_tempo"

    @property
    def native_value(self):
        """Return a human-readable combined Tempo status."""
        data = self.coordinator.data or {}
        if not data.get("tempo_configured"):
            return "Non configuré"

        color = data.get("tempo_color", "Inconnu")
        is_hc = data.get("tempo_is_hc")

        color_emoji = {"Bleu": "🔵", "Blanc": "⚪", "Rouge": "🔴"}.get(color, "❓")
        period = "HC" if is_hc else "HP"
        return f"{color_emoji} {color} {period}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        color = data.get("tempo_color", "Inconnu")
        is_hc = data.get("tempo_is_hc")
        reason = data.get("decision_reason", "")
        surplus = data.get("solar_surplus_w")
        pump_power = data.get("pump_power_w", 750)
        margin = data.get("rouge_surplus_margin_w", 50)
        required = pump_power + margin

        tempo_impact = _describe_tempo_impact(color, is_hc, reason)

        attrs = {
            "couleur": color,
            "heures_creuses": is_hc,
            "periode": "HC" if is_hc else ("HP" if is_hc is not None else "Inconnue"),
            "tempo_configure": data.get("tempo_configured", False),
            "impact_sur_pompe": tempo_impact,
            "raison_decision": reason,
            "hc_contribution_minutes_today": round(data.get("hc_contribution_minutes", 0), 1),
        }

        # Afficher les détails du surplus uniquement sur les jours rouges HP
        if color == "Rouge" and not is_hc:
            attrs.update({
                "surplus_solaire_w": round(surplus, 0) if surplus is not None else "N/A",
                "puissance_pompe_w": pump_power,
                "marge_securite_w": margin,
                "surplus_requis_w": required,
                "surplus_suffisant": (surplus is not None and surplus >= required),
                "manque_w": round(max(0, required - (surplus or 0)), 0),
            })

        return attrs


def _describe_tempo_impact(color: str, is_hc: Optional[bool], reason: str) -> str:
    """Return a human-readable explanation of Tempo's impact on the pump."""
    if "no_tempo" in reason:
        return "Tempo non configuré — pas de restriction tarifaire"
    if "solar" in reason and "rouge" not in reason:
        return f"Solaire disponible — Tempo ({color}) ignoré"
    if "bleu" in reason:
        return "Jour Bleu — fonctionnement libre sur réseau"
    if "blanc_hc" in reason:
        return "Jour Blanc HC — tarif acceptable, pompe autorisée"
    if "blanc_hp_blocked" in reason:
        return "Jour Blanc HP — tarif élevé, pompe bloquée (attente solaire ou HC)"
    if "blanc_hp_allowed" in reason:
        return "Jour Blanc HP — autorisé manuellement dans les options"
    if "blanc_hp_solar" in reason:
        return "Jour Blanc HP — surplus solaire suffisant"
    if "rouge_hc_allowed" in reason:
        return "Jour Rouge HC — autorisé (tarif HC seulement)"
    if "rouge_hc_blocked" in reason:
        return "Jour Rouge HC — bloqué par configuration"
    if "rouge_hp_surplus_ok" in reason:
        # Extraire la valeur du surplus depuis le code raison
        try:
            surplus_str = reason.split("rouge_hp_surplus_ok_")[1].replace("W", "")
            return f"Jour Rouge HP — surplus solaire suffisant ({surplus_str} W disponibles)"
        except (IndexError, ValueError):
            return "Jour Rouge HP — surplus solaire suffisant"
    if "rouge_hp_surplus_insufficient" in reason:
        try:
            parts = reason.split("_")
            surplus = parts[5].replace("W", "")
            needed = parts[7].replace("W", "")
            return f"Jour Rouge HP — surplus insuffisant ({surplus} W dispo, {needed} W requis)"
        except (IndexError, ValueError):
            return "Jour Rouge HP — surplus solaire insuffisant, pompe bloquée"
    if "rouge_hp_no_sensor" in reason:
        return "Jour Rouge HP — capteurs indisponibles, pompe bloquée par précaution"
    return f"Décision : {reason}"


class PoolWaterHeaterSensor(PoolBaseSensor):
    """
    Water heater (ballon ECS) priority status sensor.

    Shows whether the ballon has reached the minimum temperature threshold
    required before the pool pump is allowed to claim solar surplus.
    """

    _attr_name = "Pool Filtration — Priorité Ballon ECS"
    _attr_icon = "mdi:water-boiler"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_water_heater"

    @property
    def native_value(self):
        """Return current water heater temperature, or None if not configured."""
        data = self.coordinator.data or {}
        if not data.get("water_heater_configured"):
            return None
        return data.get("water_heater_temp")

    @property
    def icon(self) -> str:
        data = self.coordinator.data or {}
        if not data.get("water_heater_configured"):
            return "mdi:water-boiler-off"
        unlocked = data.get("water_heater_unlocked", False)
        temp = data.get("water_heater_temp")
        min_temp = data.get("water_heater_min_temp", 50)
        if temp is None:
            return "mdi:water-boiler-alert"
        if unlocked:
            return "mdi:water-boiler-auto"   # ballon chaud, pompe autorisée
        return "mdi:water-boiler"            # ballon en chauffe, pompe en attente

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}

        if not data.get("water_heater_configured"):
            return {"configured": False, "note": "Capteur ballon non configuré — priorité désactivée"}

        temp = data.get("water_heater_temp")
        min_temp = data.get("water_heater_min_temp", 50.0)
        unlock_threshold = data.get("water_heater_unlock_threshold", 52.0)
        unlocked = data.get("water_heater_unlocked", False)
        reason = data.get("decision_reason", "")

        # Status message
        if temp is None:
            status = "Capteur indisponible — priorité ignorée"
        elif unlocked:
            status = f"✅ Ballon chaud ({temp:.1f}°C ≥ {min_temp:.0f}°C) — pompe autorisée"
        else:
            manque = unlock_threshold - (temp or 0)
            status = (
                f"🔥 Ballon en chauffe ({temp:.1f}°C, besoin de {unlock_threshold:.0f}°C) "
                f"— pompe bloquée (encore {manque:.1f}°C)"
            )

        # Pompe bloquée à cause du ballon ?
        pump_blocked_by_heater = "water_heater_priority" in reason or "water_heater_relocked" in reason

        return {
            "configured": True,
            "temperature_actuelle_c": temp,
            "seuil_minimum_c": min_temp,
            "seuil_deverrouillage_c": unlock_threshold,
            "pompe_autorisee": unlocked,
            "pompe_bloquee_par_ballon": pump_blocked_by_heater,
            "statut": status,
        }
