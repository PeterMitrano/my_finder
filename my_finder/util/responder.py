def is_valid(response):
    try:
        if not response['response']['outputSpeech']['ssml']:
            return False
        if response['response']['outputSpeech']['type'] != 'SSML':
            return False
        if "Something went wrong" in response['response']['outputSpeech'][
                'ssml']:
            return False
    except Exception:
        return False

    return True


def nop():
    return fini({}, {})


def tell(speech_output):
    response = {'outputSpeech': outputSpeech(speech_output),
                'shouldEndSession': True}
    # session attributes don't me anything for tell's
    return fini({}, response)


def ask(speech_output, session_attributes):
    response = {
        'outputSpeech': outputSpeech(speech_output),
        'repromptSpeech': outputSpeech(speech_output),
        'shouldEndSession': False
    }
    return fini(session_attributes, response)


def outputSpeech(ssml):
    return {"type": "SSML", "ssml": "<speak>" + ssml + "</speak>"}


def fini(attributes, response):
    return {"version": "1.0",
            "sessionAttributes": attributes,
            "response": response}
