"""Select entity for Pool Filtration operating mode."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_AUTO, MODE_SOLAR, MODE_MANUAL, MODE_OFF
from .coordinator import PoolFiltrationCoordinator

MODE_OPTIONS = {
    MODE_AUTO:   "🤖 Automatique",
    MODE_SOLAR:  "☀️ Solaire uniquement",
    MODE_MANUAL: "🔧 Manuel",
    MODE_OFF:    "⛔ Arrêt forcé",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolFiltrationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PoolModeSelect(coordinator, entry)])


class PoolModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity to choose the filtration operating mode."""

    _attr_name = "Pool Filtration — Mode de fonctionnement"
    _attr_icon = "mdi:cog-outline"
    _attr_options = list(MODE_OPTIONS.values())

    def __init__(self, coordinator: PoolFiltrationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_mode_select"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart Pool Filtration Manager",
        }

    @property
    def current_option(self) -> str:
        data = self.coordinator.data or {}
        mode = data.get("mode", MODE_AUTO)
        return MODE_OPTIONS.get(mode, MODE_OPTIONS[MODE_AUTO])

    async def async_select_option(self, option: str) -> None:
        """Change mode when user selects from dropdown."""
        # Reverse lookup: label → key
        mode_key = next(
            (k for k, v in MODE_OPTIONS.items() if v == option),
            MODE_AUTO
        )
        await self.coordinator.set_mode(mode_key)
