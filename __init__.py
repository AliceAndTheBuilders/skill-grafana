import logging

from aiohttp.web import Request
from jinja2 import Template

from opsdroid.matchers import match_webhook
from opsdroid.events import Message


_LOGGER = logging.getLogger(__name__)


def format_alert_message(request, config):
    """Format the alert message based on configuration and request data using Jinja2."""
    # Get the message template from config or use default
    firing_template_str = config.get("message_firing_template", "[FIRING] {{title}}\n{{message}}")
    resolved_template_str = config.get("message_resolved_template", "[RESOLVED] {{title}}\n{{message}}")

    _LOGGER.debug(f"Firing_template_str: {firing_template_str}")
    _LOGGER.debug(f"Resolved_template_str: {resolved_template_str}")

    firing_template = Template(firing_template_str)
    resolved_template = Template(resolved_template_str)

    alert_messages = []

    try:
        for alert in request["alerts"]:
            if alert["status"] == "firing":
                _LOGGER.debug(f"Processing alert as firing {alert}")
                template = firing_template
            else:
                _LOGGER.debug(f"Processing alert as resolved {alert}")
                template = resolved_template

            alert_messages.append(template.render(**alert))
    except Exception as e:
        _LOGGER.warning(f"Error in template formatting: {e}")
        alert_messages.append(f"{request.get('title', 'Alert')}\n{request.get('message', 'No message provided')}")

    return "\n\n".join(alert_messages)


@match_webhook("alert")
async def process_alert_webhook(opsdroid, config, message):
    if type(message) is not Message and type(message) is Request:
        # Capture the request json data and set message to a default message
        request = await message.json()
        _LOGGER.debug(f"Request {request}")
        _LOGGER.debug(f"Config {config}")
        connector = opsdroid.default_connector
        room = config.get("room", connector.default_room)
        message = Message("", None, room, connector)

        # Format and respond with the alert message
        formatted_message = format_alert_message(request, config)
        await message.respond(formatted_message)
