"""Switch entity for Pool Filtration manual override."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_MANUAL, MODE_AUTO
from .coordinator import PoolFiltrationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolFiltrationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PoolManualOverrideSwitch(coordinator, entry)])


class PoolManualOverrideSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to manually force the pump on/off, bypassing automation."""

    _attr_name = "Pool Filtration — Forçage manuel"
    _attr_icon = "mdi:water-pump"

    def __init__(self, coordinator: PoolFiltrationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_manual_override"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart Pool Filtration Manager",
        }

    @property
    def is_on(self) -> bool:
        """Return True if manual pump override is active and pump should be on."""
        data = self.coordinator.data or {}
        return (
            data.get("mode") == MODE_MANUAL
            and data.get("pump_running", False)
        )

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "mode": data.get("mode"),
            "note": "Activating this switch sets mode to MANUAL and forces the pump ON. "
                    "Deactivating returns to AUTO mode.",
        }

    async def async_turn_on(self, **kwargs):
        """Force pump ON in manual mode."""
        await self.coordinator.set_manual_override(True)

    async def async_turn_off(self, **kwargs):
        """Return to AUTO mode."""
        await self.coordinator.set_mode(MODE_AUTO)
