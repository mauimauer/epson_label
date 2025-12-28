"""Binary sensors for Epson Label Printer."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EpsonPrinterCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Epson Label Printer binary sensors."""
    coordinator: EpsonPrinterCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([
        EpsonConnectivitySensor(coordinator, entry),
        EpsonPaperSensor(coordinator, entry),
    ])


class EpsonBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for Epson binary sensors."""

    def __init__(self, coordinator: EpsonPrinterCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Epson Printer {coordinator.host}",
            "manufacturer": "Epson",
            "model": "Label Printer",
        }


class EpsonConnectivitySensor(EpsonBaseBinarySensor):
    """Sensor for printer connectivity status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_connectivity"
        self._attr_name = "Connectivity"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.coordinator.data.get("online", False)


class EpsonPaperSensor(EpsonBaseBinarySensor):
    """Sensor for printer paper status."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_paper_status"
        self._attr_name = "Paper Status"

    @property
    def is_on(self) -> bool:
        """Return true if there is a problem (paper out)."""
        return self.coordinator.data.get("paper_error", False)
