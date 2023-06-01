# -*- coding: utf-8 -*-
"""Simple fact sample app."""

import random
import logging
import json
import prompts
import boto3
import os
import visualresponse

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name, get_slot_value, get_slot, get_supported_interfaces
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective

sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

QueryDraginoLastValueInternal = "SELECT measure_value::double as temperature_internal FROM \"{}\".\"draginodata\" WHERE measure_name = 'temperature_internal' AND device = '{}' ORDER BY time DESC LIMIT 1"
QueryDraginoLastExternal = "SELECT measure_value::double as temperature_internal FROM \"{}\".\"draginodata\" WHERE measure_name = 'temperature_external' AND device = '{}' ORDER BY time DESC LIMIT 1"
Queryesp8266tempsensorsLast = "SELECT measure_value::double as temperature FROM \"{}\".\"esp8266tempsensors\" WHERE (measure_name = 'temperature') AND (device = '{}') ORDER BY time DESC LIMIT 1"
Queryesp8266simpletempsensorsLast = "SELECT measure_value::double as temperature FROM \"{}\".\"esp8266simpletempsensors\" WHERE (measure_name = 'temperature') AND (device = '{}') ORDER BY time DESC LIMIT 1"

QueryDraginoMaxValueInternal = "SELECT MAX(measure_value::double) as temperature_internal FROM \"{}\".\"draginodata\" WHERE measure_name = 'temperature_internal' AND device = '{}' AND time >= ago(24h)"
QueryDraginoMaxExternal = "SELECT MAX(measure_value::double) as temperature_internal FROM \"{}\".\"draginodata\" WHERE measure_name = 'temperature_external' AND device = '{}' AND time >= ago(24h)"
Queryesp8266tempsensorsMax = "SELECT MAX(measure_value::double) AS temperature FROM \"{}\".\"esp8266tempsensors\" WHERE (measure_name = 'temperature') AND (device = '{}') AND time >= ago(24h)"
Queryesp8266simpletempsensorsMax = "SELECT MAX(measure_value::double) as temperature FROM \"{}\".\"esp8266simpletempsensors\" WHERE (measure_name = 'temperature') AND (device = '{}') AND time >= ago(24h)"

QueryDraginoMinValueInternal = "SELECT MIN(measure_value::double) as temperature_internal FROM \"{}\".\"draginodata\" WHERE measure_name = 'temperature_internal' AND device = '{}' AND time >= ago(24h)"
QueryDraginoMinExternal = "SELECT MIN(measure_value::double) as temperature_internal FROM \"{}\".\"draginodata\" WHERE measure_name = 'temperature_external' AND device = '{}' AND time >= ago(24h)"
Queryesp8266tempsensorsMin = "SELECT MIN(measure_value::double) AS temperature FROM \"{}\".\"esp8266tempsensors\" WHERE (measure_name = 'temperature') AND (device = '{}') AND time >= ago(24h)"
Queryesp8266simpletempsensorsMin = "SELECT MIN(measure_value::double) as temperature FROM \"{}\".\"esp8266simpletempsensors\" WHERE (measure_name = 'temperature') AND (device = '{}') AND time >= ago(24h)"


CorrespondanceTable = {  
 "chambre de sandrine":{"name":"chambresandrine","query":Queryesp8266simpletempsensorsLast,"query_max":Queryesp8266simpletempsensorsMax,"query_min":Queryesp8266simpletempsensorsMin,"vocable":"dans la"},
 "chambre de margaux":{"name":"esp8266TempSensor1","query":Queryesp8266tempsensorsLast, "query_max":Queryesp8266tempsensorsMax,"query_min":Queryesp8266tempsensorsMin, "vocable":"dans la"},
 "terrasse":{"name":"4e056d74-38c0-4431-8ab6-d05b3dcda891","query":QueryDraginoLastValueInternal,"query_max":QueryDraginoMaxValueInternal,"query_min":QueryDraginoMinValueInternal,"vocable":"sur la"},
 "jardin":{"name":"a0b65205-b976-40f7-8815-2f62bd3ae32c","query":QueryDraginoLastValueInternal,"query_max":QueryDraginoMaxValueInternal,"query_min":QueryDraginoMinValueInternal,"vocable":"dans le"},
 "piscine":{"name":"a0b65205-b976-40f7-8815-2f62bd3ae32c","query":QueryDraginoLastExternal, "query_max":QueryDraginoMaxExternal,"query_min":QueryDraginoMinExternal,"vocable":"de la"},
}

#class to display results on screen
class VisualHandler(AbstractRequestHandler):
    def supports_apl(self, handler_input):
        # Checks whether APL is supported by the User's device
        supported_interfaces = get_supported_interfaces(
            handler_input)
        return supported_interfaces.alexa_presentation_apl != None

    def launch_screen(self, handler_input,anAPLDocToken,anAPLDocID, aDatasource):
        # Only add APL directive if User's device supports APL
        if self.supports_apl(handler_input):
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    token=anAPLDocToken,
                    document={
                        "type": "Link",
                        "src": f"doc://alexa/apl/documents/{anAPLDocID}"
                    },
                    datasources=aDatasource
                )
            )

    def simpleVisual(self, handler_input,data):
        #connect to the timestream database
        timestream = boto3.client('timestream-query')

        #get the database name from the lambda function's environment variable
        myDatabaseName = os.environ['DATABASE_NAME']
        myDistribution = os.environ['CLOUD_FRONT_SITE']

        #setup the visual response
        myVisualResponse = visualresponse.VisualResponse()
        myVisualResponse.setTitle(data[prompts.SKILL_NAME])
        #todo: remove the static reference to the image
        myVisualResponse.setBackgroundImage("https://{}/web/skill/background.png".format(myDistribution))
        myVisualResponse.setLogo("https://{}/web/skill/icon.png".format(myDistribution))

        #reset the list
        myVisualResponse.emptyListItem()

        #add each température
        for item in CorrespondanceTable:
            query = CorrespondanceTable[item]["query"].format(myDatabaseName,CorrespondanceTable[item]["name"])
            response = timestream.query(QueryString=query)
            myTemperature = response["Rows"][0]["Data"][0]["ScalarValue"]

            query = CorrespondanceTable[item]["query_max"].format(myDatabaseName,CorrespondanceTable[item]["name"])
            response = timestream.query(QueryString=query)
            myMaxTemperature = response["Rows"][0]["Data"][0]["ScalarValue"]

            query = CorrespondanceTable[item]["query_min"].format(myDatabaseName,CorrespondanceTable[item]["name"])
            response = timestream.query(QueryString=query)
            myMinTemperature = response["Rows"][0]["Data"][0]["ScalarValue"]

            myVisualResponse.addListItem(item + " : " +  str(round(float(myTemperature)))+"°C"+" / <span color=\"blue\">"+ str(round(float(myMinTemperature))) +"°C" +"</span> / <span color=\"red\">"+ str(round(float(myMaxTemperature))) +"°C</span>")

        #add the visual response to the response
        self.launch_screen(handler_input,visualresponse.APL_DOCUMENT_TOKEN,visualresponse.APL_DOCUMENT_ID,myVisualResponse.getResponse())



class LaunchRequestHandler(VisualHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In launch request handler")
        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]
        
        self.simpleVisual(handler_input,data)

        speech = data[prompts.WELCOME_MESSAGE]

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], speech))

        
        return handler_input.response_builder.response



#Intent Handler
class TemperatureIntentHandler(VisualHandler):
    """Handler for skill launch and temperature Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("temperature")(handler_input))


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In temperature handler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        # first, we retrieve the slot value with the sensor name
        mySensorValue = get_slot(
            handler_input=handler_input, slot_name="endroit").resolutions.resolutions_per_authority[0].values[0].value.name

        #get the database name from the lambda function's environment variable
        myDatabaseName = os.environ['DATABASE_NAME']

        #connect to the timestream database
        timestream = boto3.client('timestream-query')

        #query the timestream database
        query = CorrespondanceTable[mySensorValue]["query"].format(myDatabaseName,CorrespondanceTable[mySensorValue]["name"])
        response = timestream.query(QueryString=query)

        #extract the temperature from the response
        myTemperature = response["Rows"][0]["Data"][0]["ScalarValue"]

        logger.info(response)  

        speech = data[prompts.TEMPERATURE_MESSAGE].format(CorrespondanceTable[mySensorValue]["vocable"],mySensorValue,round(float(myTemperature)))

        self.simpleVisual(handler_input,data)

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], speech))

        
        #.set_card(SimpleCard(data[prompts.SKILL_NAME], random_fact))
        return handler_input.response_builder.response

#Intent Handler
class MaxTemperatureIntentHandler(VisualHandler):
    """Handler for skill launch and temperature Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("maxtemperature")(handler_input))


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In maxtemperature handler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        # first, we retrieve the slot value with the sensor name
        mySensorValue = get_slot(
            handler_input=handler_input, slot_name="endroit").resolutions.resolutions_per_authority[0].values[0].value.name

        #get the database name from the lambda function's environment variable
        myDatabaseName = os.environ['DATABASE_NAME']

        #connect to the timestream database
        timestream = boto3.client('timestream-query')

        #query the timestream database
        query = CorrespondanceTable[mySensorValue]["query_max"].format(myDatabaseName,CorrespondanceTable[mySensorValue]["name"])
        response = timestream.query(QueryString=query)

        #extract the temperature from the response
        myTemperature = response["Rows"][0]["Data"][0]["ScalarValue"]

        logger.info(response)  

        speech = data[prompts.MAX_TEMPERATURE_MESSAGE].format(CorrespondanceTable[mySensorValue]["vocable"],mySensorValue,round(float(myTemperature)))

        self.simpleVisual(handler_input,data)

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], speech))

        
        #.set_card(SimpleCard(data[prompts.SKILL_NAME], random_fact))
        return handler_input.response_builder.response

#Intent Handler
class MinTemperatureIntentHandler(VisualHandler):
    """Handler for skill launch and temperature Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("mintemperature")(handler_input))


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In mintemperature handler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        # first, we retrieve the slot value with the sensor name
        mySensorValue = get_slot(
            handler_input=handler_input, slot_name="endroit").resolutions.resolutions_per_authority[0].values[0].value.name

        #get the database name from the lambda function's environment variable
        myDatabaseName = os.environ['DATABASE_NAME']

        #connect to the timestream database
        timestream = boto3.client('timestream-query')

        #query the timestream database
        query = CorrespondanceTable[mySensorValue]["query_min"].format(myDatabaseName,CorrespondanceTable[mySensorValue]["name"])
        response = timestream.query(QueryString=query)

        #extract the temperature from the response
        myTemperature = response["Rows"][0]["Data"][0]["ScalarValue"]

        logger.info(response)  

        speech = data[prompts.MIN_TEMPERATURE_MESSAGE].format(CorrespondanceTable[mySensorValue]["vocable"],mySensorValue,round(float(myTemperature)))

        self.simpleVisual(handler_input,data)

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], speech))

        
        #.set_card(SimpleCard(data[prompts.SKILL_NAME], random_fact))
        return handler_input.response_builder.response


class SensorListIntentHandler(VisualHandler):
    """Handler for skill launch and temperature Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("sensorlist")(handler_input))


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In sensorlist handler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech= data[prompts.SENSOR_LIST_MESSAGE].format(','.join(list(CorrespondanceTable.keys())))
        
        self.simpleVisual(handler_input,data)

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], speech))

        
        #.set_card(SimpleCard(data[prompts.SKILL_NAME], random_fact))
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.HELP_MESSAGE]
        reprompt = data[prompts.HELP_REPROMPT]
        handler_input.response_builder.speak(speech).ask(
            reprompt).set_card(SimpleCard(
                data[prompts.SKILL_NAME], speech))
        return handler_input.response_builder.response



class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In CancelOrStopIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.STOP_MESSAGE]
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.

    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.FALLBACK_MESSAGE]
        reprompt = data[prompts.FALLBACK_REPROMPT]
        handler_input.response_builder.speak(speech).ask(
            reprompt)
        return handler_input.response_builder.response


class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add function to request attributes, that can load locale specific data.
    This function will be used if we want to support multilanguage
    """

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale[:2]))

        # localized strings stored in language_strings.json
        with open("language_strings.json") as language_prompts:
            language_data = json.load(language_prompts)
        # set default translation data to broader translation
        data = language_data[locale[:2]]
        # if a more specialized translation exists, then select it instead
        # example: "fr-CA" will pick "fr" translations first, but if "fr-CA" translation exists,
        #          then pick that instead
        if locale in language_data:
            data.update(language_data[locale])
        handler_input.attributes_manager.request_attributes["_"] = data


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)

        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))


# Register intent handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(TemperatureIntentHandler())
sb.add_request_handler(MaxTemperatureIntentHandler())
sb.add_request_handler(MinTemperatureIntentHandler())
sb.add_request_handler(SensorListIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Register request and response interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()
