import openai

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