"""DataUpdateCoordinator for Epson Label Printer."""
import logging
from datetime import timedelta
from typing import Any, Dict

from escpos.printer import Network

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_HOST, CONF_PORT

_LOGGER = logging.getLogger(__name__)

class EpsonPrinterCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Epson Printer data."""

    def __init__(self, hass: HomeAssistant, entry_data: Dict[str, Any]) -> None:
        """Initialize."""
        self.host = entry_data[CONF_HOST]
        self.port = entry_data[CONF_PORT]
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"Epson Printer {self.host}",
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the printer."""
        return await self.hass.async_add_executor_job(self._update_data)

    def _update_data(self) -> Dict[str, Any]:
        """Fetch data synchronously."""
        data = {
            "online": False,
            "paper_error": False
        }
        
        p = None
        try:
            # Connect
            p = Network(self.host, port=self.port, timeout=5)
            
            # Check online status
            if p.is_online():
                data["online"] = True
                
                # Check paper status
                # 2: Paper is adequate. 1: Paper ending. 0: No paper.
                status = p.paper_status()
                if status == 2:
                    data["paper_error"] = False
                else:
                    data["paper_error"] = True
            else:
                 data["online"] = False

        except Exception as err:
            # If connection fails, it's offline
            data["online"] = False
            _LOGGER.debug("Printer %s offline or unreachable: %s", self.host, err)
        finally:
            if p:
                try:
                    p.close()
                except Exception:
                    pass
        
        return data
