"""Support for the Rhasspy speech service."""
import asyncio
from http import HTTPStatus
import logging

import aiohttp
import async_timeout
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.tts import PLATFORM_SCHEMA, Provider
from homeassistant.const import (
    CONF_URL,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

CONF_DEFAULT_LANG = "default_language"

SUPPORT_LANGUAGES = [
    "de",
    "en",
    "es",
    "fr",
    "it",
    "de-DE",
    "en-US",
    "en-GB",
    "es-ES",
    "fr-FR",
    "it-IT",
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL): cv.string,
        vol.Required(CONF_DEFAULT_LANG): cv.string,
    },
)


async def async_get_engine(hass, config, discovery_info=None):
    """Set up Rhasspy speech component."""
    return RhasspyProvider(hass, config)


class RhasspyProvider(Provider):
    """The Rhasspy speech API provider."""

    def __init__(self, hass, config):
        """Init Rhasspy TTS service."""
        _LOGGER.info("Rhasspy config: %s", config)
        self.hass = hass
        self._baseurl = config.get(CONF_URL)
        self._def_lang = config.get(CONF_DEFAULT_LANG)
        self.name = "Rhasspy"

        self._tts_url = f"{self._baseurl}/api/text-to-speech"

    @property
    def default_language(self):
        """Return the default language."""
        return self._def_lang

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    async def async_get_tts_audio(self, message, language, options=None):
        """Load TTS from Rhasspy."""
        websession = async_get_clientsession(self.hass)
        actual_language = language

        try:
            async with async_timeout.timeout(10):
                url_param = {
                    "language": actual_language,
                    "play": "false",
                }

                request = await websession.post(
                    self._tts_url, params=url_param, data=message
                )

                if request.status != HTTPStatus.OK:
                    _LOGGER.error(
                        "Error %d on load URL %s", request.status, request.url
                    )
                    return (None, None)
                data = await request.read()

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Timeout for Rhasspy API")
            return (None, None)

        return ("wav", data)
