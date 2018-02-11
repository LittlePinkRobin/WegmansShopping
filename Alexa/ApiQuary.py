from __future__ import print_function
import http.client, urllib.request, urllib.parse, urllib.error, base64, json, requests

headers = {
    # Request headers
    'Product-Subscription-Key': '9a70369bd4304f958d5e75991d8f9bdf',
}

params = urllib.parse.urlencode({
})


def get_lists_metadata(session):
    r = 'permissions' in session['user']
    if not r:
        print('no Perms')
        return None
    print(session['user']['permissions']['consentToken'])
    token = session['user']['permissions']['consentToken']
    print(token)
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'json'
    }

    print("BEFORE HTTP")
    conn = http.client.HTTPSConnection('api.amazonalexa.com', 443)
    conn.request('GET', '/v2/householdlists/', "{body}", headers)
    response = conn.getresponse()
    print('BEFORE STATUS')
    status = response.status
    print(status)
    if status == 403:
        print("Empty List")
        return None

    data = response.read().decode('utf-8')
    jsonresponse = json.loads(data)
    return jsonresponse


def getList(session):
    r = 'permissions' in session['user']
    if not r:
        return None
    token = session['user']['permissions']['consentToken']

    response = get_lists_metadata(session)
    todo_path = None
    for i in range(len(response['lists'])):
        if response['lists'][i]['name'] == 'Alexa shopping list':
            for j in range(len(response['lists'][i]['statusMap'])):
                if response['lists'][i]['statusMap'][j]['status'] == 'active':
                    todo_path = response['lists'][i]['statusMap'][j]['href']
                    break
        break
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'json'
    }
    conn = http.client.HTTPSConnection('api.amazonalexa.com', 443)
    conn.request('GET', todo_path, "{body}", headers)
    response = conn.getresponse();
    status = response.status
    if status == 403:
        print("permissions are not granted");
        return None;
    elif status == 400:
        print('YOU FUCKED UP AGAIN, ROBIN')

    data = response.read().decode('utf-8')
    jsonresponse = json.loads(data)
    return jsonresponse


def update_list(session, name, sku):
    r = 'permissions' in session['user']
    if not r:
        return None
    token = session['user']['permissions']['consentToken']

    response = get_lists_metadata(session)
    todo_path = None
    for i in range(len(response['lists'])):
        if response['lists'][i]['name'] == 'Alexa shopping list':
            for j in range(len(response['lists'][i]['statusMap'])):
                if response['lists'][i]['statusMap'][j]['status'] == 'active':
                    todo_path = response['lists'][i]['listID']
                break
        break
    params = {"value": name + ' ' + sku,
                                     "status": "active"}
    params = json.dumps(params)
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'json'
    }
    print(todo_path)
    conn = http.client.HTTPSConnection('api.amazonalexa.com', 443)
    conn.request('POST', 'v2/householdlists/%s/items' % todo_path, params, headers)
    response = requests.post('https://api.amazonalexa.comAlexa/ApiQuary.py:2' % todo_path, data= {"value": name + ' ' + sku,
                                     "status": "active"} )
    status = response.status
    print(status)
    if status == 403:
        print("permissions are not granted");
        return None;
    elif status == 400:
        print('YOU FUCKED UP AGAIN, ROBIN')
    data = response.read().decode('utf-8')
    jsonresponse = json.loads(data)
    print(jsonresponse)


def quary(intent, session):
    print()
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = None

    if 'Item' in intent['slots']:
        print("ITEM EXISTS")
        food_to_add = intent['slots']['Item']['value']
        print(food_to_add)

        speech_output = food_to_add + \
                        " Added to cart "
        try:
            conn = http.client.HTTPSConnection('api.wegmans.io')
            conn.request("GET", "/product/products/search?criteria=%s&%s" % (food_to_add, params), "{body}", headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            jsonresponse = json.loads(data)
            jsonresponse = (jsonresponse['results'][0])
            print(jsonresponse)
            conn.close()
            print(get_lists_metadata(session))
            session_attributes = create_favorite_color_attributes(jsonresponse['sku'])
            update_list(session, food_to_add, jsonresponse['sku'])
            return build_response(session_attributes, build_speechlet_response(
                intent['name'], speech_output, reprompt_text, should_end_session))
        except Exception as e:
            print(e)
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
    else:
        speech_output = "I'm not sure what you want to add. " \
                        "Please try again."


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Wegmam's Shopping cart. "
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = None
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using Wegman's Shopping cart. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_favorite_color_attributes(sku):
    return {"sku": sku}


def set_color_in_session(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'Color' in intent['slots']:
        favorite_color = intent['slots']['Color']['value']
        session_attributes = create_favorite_color_attributes(favorite_color)
        speech_output = "I now know your favorite color is " + \
                        favorite_color + \
                        ". You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
        reprompt_text = "You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your favorite color is. " \
                        "You can tell me your favorite color by saying, " \
                        "my favorite color is red."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "AddToCart":
        return quary(intent, session)
    else:
        print("invalid intent")
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("END SESSION")
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print('HANDLING EVENT')
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")


    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
