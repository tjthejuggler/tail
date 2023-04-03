import openai
import regex
from utilities import *

def verify_jsonness(input_string):
    json_pattern = r'\{(?:[^{}]|(?R))*\}'
    json_matches = regex.findall(json_pattern, input_string)
    if json_matches:
        includes_dict = True
        only_dict = len(json_matches) == 1 and json_matches[0] == input_string
        included_dict = json_matches[0]
    else:
        includes_dict = False
        only_dict = False
        included_dict = None

    return includes_dict, only_dict, included_dict

def jsonify_response(response):
    jsonified_response, tokens = send_request([{"role": "user", "content":"Convert the following string into a JSON object with 3 keys: 'inner' for any information that is not outwardly apparent, such as the characters inner dialogue, 'speak' for anything that the character says, and 'action' for any actions that the character takes.\n\n"+response+"\n\nRespond only with the JSON object."}])
    print("tokens", tokens)
    return(jsonified_response, tokens)

def ask_universe_assistant(action):
    response, tokens = chatgpt_req.send_request([{"role": "user", "content":"I am going to give you an action. It is your job to tell me if this action would typically have a result that would add new information to the situation.\n\n"+action+"\n\nRespond with a single word, yes or no."}])
    print("ask_universe_assistant")
    print("tokens", tokens)
    return(response, tokens)

def tell_universe(memory, request_message, story_seed_file):
    request_message = replace_names_with_character_numbers(request_message, story_seed_file)
    print("request_message after new replace", request_message)
    if request_message:
        memory.append(["user",request_message])
    print("tell_universe memory.read()", memory.read())
    response, tokens = send_request(memory.read())
    print('tell_universe response', response)
    memory.append(["assistant",response])
    return(memory, memory.read()[-1]['content'], tokens)

def tell_character(memory, request_message):
    if request_message:
        memory.append(["user",request_message+"\nRespond with a single JSON object."])
    print("tell_char_bot memory.read()", memory.read())
    response, tokens = send_request(memory.read())
    print('tell_chracter response', response)
    contains_dict, only_dict, response = verify_jsonness(response)
    print("contains_dict, only_dict, response", contains_dict, only_dict, response)
    if not contains_dict:
        response, jsonify_tokens = jsonify_response(response)
        tokens += jsonify_tokens
    memory.append(["assistant",response])
    return(memory, memory.read()[-1]['content'], tokens)

def send_request(request_message):
    with open('api_key.txt', 'r') as f:
        api_key = f.read().strip()
    openai.api_key = (api_key)
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=request_message
    )
    print("response!!!!!!!!!!!!", response)
    bot_says = response["choices"][0]["message"]["content"]
    tokens = response["usage"]["total_tokens"]
    return(bot_says, tokens)


# print(send_request([
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": "Who won the world series in 2000?"},
#         ]))

#print(response)