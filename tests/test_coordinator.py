"""Tests pour le coordinateur Pool Filtration."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date

from custom_components.pool_filtration.coordinator import (
    calculate_target_duration,
    PoolFiltrationCoordinator,
)
from custom_components.pool_filtration.const import (
    MODE_AUTO, MODE_SOLAR, MODE_OFF, MODE_MANUAL,
)


# ------------------------------------------------------------------
# Tests calculate_target_duration
# ------------------------------------------------------------------

class TestCalculateTargetDuration:
    def test_cold_water_minimum(self):
        """Eau froide → durée minimale."""
        assert calculate_target_duration(5) == 1.0

    def test_warm_water_maximum(self):
        """Eau très chaude → durée maximale."""
        assert calculate_target_duration(35) == 12.0

    def test_exact_table_value(self):
        """Valeur exacte de la table → résultat exact."""
        assert calculate_target_duration(24) == 6.0

    def test_interpolation_between_points(self):
        """Interpolation linéaire entre deux points."""
        # Entre 20°C (4h) et 22°C (5h) → 21°C = 4.5h
        result = calculate_target_duration(21)
        assert abs(result - 4.5) < 0.01

    def test_hot_water(self):
        """Eau chaude → durée longue."""
        duration = calculate_target_duration(28)
        assert duration == 9.0

    def test_increases_with_temperature(self):
        """La durée augmente avec la température."""
        durations = [calculate_target_duration(t) for t in [15, 20, 25, 30]]
        assert durations == sorted(durations)


# ------------------------------------------------------------------
# Tests coordinator decision logic
# ------------------------------------------------------------------

@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "pump_switch": "switch.pompe",
        "water_temp_sensor": "sensor.temp_piscine",
        "solar_power_sensor": "sensor.solaire",
        "grid_consumption_sensor": "sensor.reseau",
    }
    entry.options = {}
    return entry


@pytest.fixture
def coordinator(mock_hass, mock_entry):
    coord = PoolFiltrationCoordinator(mock_hass, mock_entry)
    coord._store = AsyncMock()
    coord._store.async_save = AsyncMock()
    coord._store.async_load = AsyncMock(return_value=None)
    return coord


class TestCoordinatorMode:
    def test_default_mode_is_auto(self, coordinator):
        assert coordinator.mode == MODE_AUTO

    @pytest.mark.asyncio
    async def test_set_mode_solar(self, coordinator):
        await coordinator.set_mode(MODE_SOLAR)
        assert coordinator.mode == MODE_SOLAR

    @pytest.mark.asyncio
    async def test_set_mode_off(self, coordinator):
        await coordinator.set_mode(MODE_OFF)
        assert coordinator.mode == MODE_OFF

    @pytest.mark.asyncio
    async def test_set_invalid_mode_raises(self, coordinator):
        with pytest.raises(ValueError):
            await coordinator.set_mode("invalid_mode")


class TestShouldPumpRun:
    def _make_state(self, value):
        s = MagicMock()
        s.state = str(value)
        return s

    def _setup_sensors(self, coordinator, temp=24.0, solar=1500.0):
        def get_state(entity_id):
            if "temp" in entity_id:
                return self._make_state(temp)
            if "solaire" in entity_id:
                return self._make_state(solar)
            return None
        coordinator.hass.states.get = get_state

    def test_mode_off_never_runs(self, coordinator):
        coordinator._mode = MODE_OFF
        self._setup_sensors(coordinator)
        assert coordinator._should_pump_run() is False

    def test_solar_mode_runs_with_solar(self, coordinator):
        coordinator._mode = MODE_SOLAR
        self._setup_sensors(coordinator, solar=1500)
        # Dans la plage horaire (mock hour = 0, hors plage par défaut)
        # On teste juste la logique solaire
        with patch("custom_components.pool_filtration.coordinator.dt_util") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 10
            mock_now.minute = 0
            mock_dt.now.return_value = mock_now
            assert coordinator._should_pump_run() is True

    def test_solar_mode_stops_without_solar(self, coordinator):
        coordinator._mode = MODE_SOLAR
        self._setup_sensors(coordinator, solar=100)  # Sous le seuil
        with patch("custom_components.pool_filtration.coordinator.dt_util") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 10
            mock_now.minute = 0
            mock_dt.now.return_value = mock_now
            assert coordinator._should_pump_run() is False

    def test_quota_reached_stops_pump(self, coordinator):
        coordinator._mode = MODE_AUTO
        coordinator._daily_runtime_minutes = 999  # Quota largement dépassé
        self._setup_sensors(coordinator)
        assert coordinator._should_pump_run() is False

    def test_outside_hours_stops_pump(self, coordinator):
        coordinator._mode = MODE_AUTO
        self._setup_sensors(coordinator)
        with patch("custom_components.pool_filtration.coordinator.dt_util") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 3   # 3h du matin, hors plage
            mock_now.minute = 0
            mock_dt.now.return_value = mock_now
            assert coordinator._should_pump_run() is False


class TestDailyReset:
    def test_resets_on_new_day(self, coordinator):
        from datetime import date
        coordinator._daily_runtime_minutes = 250.0
        coordinator._solar_contribution_minutes = 120.0
        coordinator._last_reset_date = date(2024, 1, 1)

        with patch("custom_components.pool_filtration.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = MagicMock(
                date=MagicMock(return_value=date(2024, 1, 2))
            )
            # Appel direct de la méthode interne
            coordinator._last_reset_date = date(2024, 1, 1)

            # Simuler un nouveau jour
            from homeassistant.util import dt as real_dt
            today = real_dt.now().date()
            coordinator._last_reset_date = date(2000, 1, 1)  # vieille date
            coordinator._check_daily_reset()

            assert coordinator._daily_runtime_minutes == 0.0
            assert coordinator._solar_contribution_minutes == 0.0
