"""
The Epson Label Printer integration."""
import logging
import re
from functools import partial

import voluptuous as vol
from escpos.printer import Network

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, service
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import EpsonPrinterCoordinator

_LOGGER = logging.getLogger(__name__)

# Service Schema
SERVICE_PRINT_LABEL = "print_label"
SERVICE_PRINT_LABEL_EXTENDED = "print_label_extended"

ATTR_TEXT = "text"
ATTR_SIZE = "size"
ATTR_CUT = "cut"
ATTR_FEED_LINES = "feed_lines"
ATTR_DEVICE_ID = "device_id"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): vol.Any(cv.string, [cv.string]),
        vol.Optional(ATTR_SIZE, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Optional(ATTR_CUT, default=True): cv.boolean,
        vol.Optional(ATTR_FEED_LINES, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=20)),
        vol.Optional(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SCHEMA_EXTENDED = vol.Schema(
    {
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Epson Label Printer component."""
    
    async def get_target_entries(call):
        """Helper to get target config entries from service call."""
        device_ids = call.data.get(ATTR_DEVICE_ID)
        config_entries = []
        
        if device_ids:
            registry = dr.async_get(hass)
            for device_id in device_ids:
                device = registry.async_get(device_id)
                if device:
                    for entry_id in device.config_entries:
                        entry = hass.config_entries.async_get_entry(entry_id)
                        if entry and entry.domain == DOMAIN:
                            config_entries.append(entry)
        
        if not config_entries:
            all_entries = hass.config_entries.async_entries(DOMAIN)
            if all_entries:
                config_entries = all_entries
            else:
                _LOGGER.warning("No Epson Label Printers configured.")
                return []
        
        return config_entries

    async def handle_print_label(call: ServiceCall):
        """Handle the print_label service."""
        text = call.data.get(ATTR_TEXT)
        size = call.data.get(ATTR_SIZE)
        cut = call.data.get(ATTR_CUT)
        feed_lines = call.data.get(ATTR_FEED_LINES)
        
        entries = await get_target_entries(call)
        if not entries:
            return

        if isinstance(text, str):
            text = [text]

        for entry in entries:
            host = entry.data[CONF_HOST]
            port = entry.data[CONF_PORT]
            
            await hass.async_add_executor_job(
                _print_job, host, port, text, size, cut, feed_lines
            )

    async def handle_print_label_extended(call: ServiceCall):
        """Handle the print_label_extended service."""
        text = call.data.get(ATTR_TEXT)
        
        entries = await get_target_entries(call)
        if not entries:
            return

        for entry in entries:
            host = entry.data[CONF_HOST]
            port = entry.data[CONF_PORT]
            
            await hass.async_add_executor_job(
                _print_job_extended, host, port, text
            )

    hass.services.async_register(
        DOMAIN, SERVICE_PRINT_LABEL, handle_print_label, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PRINT_LABEL_EXTENDED, handle_print_label_extended, schema=SERVICE_SCHEMA_EXTENDED
    )
    return True

def _print_job(host, port, text, size, cut, feed_lines):
    """Execute the print job."""
    try:
        p = Network(host, port=port)
        p.set(width=size, height=size)
        for line in text:
            p.text(f"{line}\n")
        
        if feed_lines > 0:
            p.text("\n" * feed_lines)
            
        if cut:
            p.cut()
        
        p.close()
    except Exception as e:
        _LOGGER.error("Error printing to %s:%s - %s", host, port, e)

def _print_job_extended(host, port, text):
    """Execute the extended print job with markup."""
    try:
        p = Network(host, port=port)
        
        # Split by commands: $CMD(args)
        # We use a regex that captures:
        # 1. Text before the command
        # 2. The command name
        # 3. The arguments
        # pattern = r"(.*?)\$([A-Z0-9_]+)\((.*?)\)(.*)" 
        # The above is not iterative. We need finditer.
        
        pattern = re.compile(r"\$([A-Z0-9_]+)\((.*?)\)")
        
        last_pos = 0
        for match in pattern.finditer(text):
            # Print text before command
            pre_text = text[last_pos:match.start()]
            if pre_text:
                p.text(pre_text)
            
            cmd = match.group(1)
            args_str = match.group(2)
            args = [arg.strip() for arg in args_str.split(",")] if args_str else []
            
            _execute_command(p, cmd, args)
            
            last_pos = match.end()
            
        # Print remaining text
        remaining_text = text[last_pos:]
        if remaining_text:
            p.text(remaining_text)
            
        p.close()
    except Exception as e:
        _LOGGER.error("Error printing extended job to %s:%s - %s", host, port, e)

def _execute_command(p, cmd, args):
    """Execute a single markup command."""
    try:
        if cmd == "SIZE":
            w = int(args[0]) if len(args) > 0 else 1
            h = int(args[1]) if len(args) > 1 else w
            p.set(width=w, height=h)
            
        elif cmd == "ALIGN":
            align = args[0].lower() if len(args) > 0 else "left"
            if align in ["left", "center", "right"]:
                p.set(align=align)
                
        elif cmd == "BOLD":
            val = args[0].lower() == "true" if len(args) > 0 else True
            p.set(bold=val)
            
        elif cmd == "INVERT":
            val = args[0].lower() == "true" if len(args) > 0 else True
            p.set(invert=val)
            
        elif cmd == "FEED":
            lines = int(args[0]) if len(args) > 0 else 1
            p.text("\n" * lines)
            
        elif cmd == "CUT":
            p.cut()
            
        elif cmd == "BARCODE":
            # $BARCODE(data, type, width, height)
            if len(args) >= 2:
                data = args[0]
                bc_type = args[1]
                width = int(args[2]) if len(args) > 2 else 3
                height = int(args[3]) if len(args) > 3 else 100
                p.barcode(data, bc_type, width=width, height=height, align_ct=False)
                
        elif cmd == "QR":
            if len(args) >= 1:
                data = args[0]
                size = int(args[1]) if len(args) > 1 else 3 # Default size
                p.qr(data, size=size)
                
        else:
            _LOGGER.warning("Unknown command: %s", cmd)
            
    except Exception as e:
        _LOGGER.warning("Failed to execute command %s(%s): %s", cmd, args, e)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Epson Label Printer from a config entry."""
    
    # Register Device
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Epson Printer {entry.data[CONF_HOST]}",
        manufacturer="Epson",
        model="Label Printer",
    )
    _LOGGER.debug("Registered device: %s", device.name)

    hass.data.setdefault(DOMAIN, {})
    
    coordinator = EpsonPrinterCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "data": entry.data,
        "coordinator": coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # If no more entries, remove services
        if not hass.data[DOMAIN]:
             hass.services.async_remove(DOMAIN, SERVICE_PRINT_LABEL)
             hass.services.async_remove(DOMAIN, SERVICE_PRINT_LABEL_EXTENDED)
             
    return unload_ok
