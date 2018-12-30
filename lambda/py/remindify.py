# -*- coding: utf-8 -*-

# This is a simple Reminder Alexa Skill, built using
# the decorators approach in skill builder.
import logging

from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.skill_builder import SkillBuilder, CustomSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.services import ServiceException
from ask_sdk_model.services.reminder_management import Trigger, TriggerType, AlertInfo, SpokenInfo, SpokenText, \
    PushNotification, PushNotificationStatus, ReminderRequest

from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard
from ask_sdk_model import Response

sb = CustomSkillBuilder(api_client=DefaultApiClient())  # required to use remiders

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REQUIRED_PERMISSIONS = ["alexa::alerts:reminders:skill:readwrite"]
TIME_ZONE_ID = 'America/Chicago'


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput) -> Response:
    """Handler for Skill Launch."""
    speech_text = "Welcome to the Alexa Skills Kit, you can say notify me."

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Welcome", speech_text)).set_should_end_session(
        False).response


@sb.request_handler(can_handle_func=is_intent_name("NotifyMeIntent"))
def notify_me_intent_handler(handler_input: HandlerInput) -> Response:
    """Handler for Notify Me Intent."""
    logging.info("running notify_me_intent_handler()")
    rb = handler_input.response_builder
    request_envelope = handler_input.request_envelope
    permissions = request_envelope.context.system.user.permissions
    reminder_service = handler_input.service_client_factory.get_reminder_management_service()

    if not (permissions and permissions.consent_token):
        logging.info("user hasn't granted reminder permissions")
        return rb.speak("Please give permissions to set reminders using the alexa app.") \
            .set_card(AskForPermissionsConsentCard(permissions=REQUIRED_PERMISSIONS)) \
            .response

    notification_time = "2018-12-30T17:50:00.00"
    trigger = Trigger(TriggerType.SCHEDULED_ABSOLUTE, notification_time, time_zone_id=TIME_ZONE_ID)
    text = SpokenText(locale='en-US', ssml='<speak>This is your reminder</speak>', text='This is your reminder')
    alert_info = AlertInfo(SpokenInfo([text]))
    push_notification = PushNotification(PushNotificationStatus.ENABLED)
    reminder_request = ReminderRequest(notification_time, trigger, alert_info, push_notification)

    try:
        reminder_responce = reminder_service.create_reminder(reminder_request)
    except ServiceException as e:
        # see: https://developer.amazon.com/docs/smapi/alexa-reminders-api-reference.html#error-messages
        logger.error(e)
        raise e

    return rb.speak("reminder created") \
        .set_card(SimpleCard("Notify Me", "reminder created")) \
        .set_should_end_session(True) \
        .response


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name("AMAZON.CancelIntent")(handler_input) or
    is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input: HandlerInput) -> Response:
    """Single handler for Cancel and Stop Intent."""
    speech_text = "Goodbye!"

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Remindify", speech_text)).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input: HandlerInput) -> Response:
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    speech = (
        "The remindify skill can't help you with that.  "
        "You can say hello!!")
    reprompt = "You can say notify me to create a reminder."
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input: HandlerInput) -> Response:
    """Handler for Session End."""
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input: HandlerInput, exception: Exception) -> Response:
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    logger.error(exception, exc_info=True)

    speech = "Sorry, there was some problem. Please try again!!"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


handler = sb.lambda_handler()
