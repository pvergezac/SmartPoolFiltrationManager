"""Fixtures partagées pour les tests Pool Filtration."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.pool_filtration.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Active les custom components dans l'environnement de test."""
    yield


@pytest.fixture
def mock_config_entry():
    """Config entry de test."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Pool Filtration Test",
        data={
            "pump_switch": "switch.pompe_piscine",
            "water_temp_sensor": "sensor.temperature_piscine",
            "solar_power_sensor": "sensor.production_solaire",
            "grid_consumption_sensor": "sensor.consommation_reseau",
        },
        options={
            "min_solar_power": 500,
            "solar_priority": True,
            "min_daily_duration": 2,
            "max_daily_duration": 12,
            "filtration_start_hour": 8,
            "filtration_end_hour": 20,
        },
    )
