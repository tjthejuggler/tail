#There are seperate instances of chatgpt
#They are told to respond first with at least some inner dialog, and then they can also respond with speaking or action as well
#   things said and done are stored in the conversation object

from storytell.bot_memory import BotMemory
import chatgpt_req
import json

def tell_bot(memory, request_message):
    if request_message:
        memory.append(["user",request_message])
    response = chatgpt_req.send_request(memory.read())
    memory.append(["assistant",response])
    return(memory, memory.read()[-1]['content'])

def initiate_bot_memories():
    bot_memories = []
    for i in range(2):
        indiv_sum = BotMemory(i)
        bot_memories.append(indiv_sum)

    bot_instruction = "You are going to play a role-playing game. When prompted you are to respond first with a required inner dialog, and then you can also optionally respond with speaking or action as well. You must label the type of responses you are giving in a JSON key/value pair format using the keys 'inner', 'speak', and 'action'. If you speak, the value of the item must be exactly what you want to say. If you If you perform an action, then the value of the item must be a 3rd person dedscription of what you would like to do, and you must refer to yourself in the 3rd person as 'your date'."

    bot_memories[0].append(["system",bot_instruction + ' You are a 28 year old man on a first blind date which has been set up by your best friend. You are meeting at a restaurant. You are nervous. You and your date have both just sat down at the table.'])

    bot_memories[1].append(["system",bot_instruction + ' You are a 27 year old woman on a first blind date which has been set up by your co-worker. You are meeting at a restaurant. You are nervous. You and your date have both just sat down at the table.'])
    return bot_memories

def parse_response(bot, response):
    #convert response string to a json object
    response = json.loads(response)
    inner_dialog = ""
    outer_information_bot_format = ""
    outer_information_user_format = ""
    if 'inner' in response:
        inner_dialog = response['inner']
    if 'speak' in response:
        outer_information_bot_format = 'Your date says, "'+response['speak']+ '".'
        outer_information_user_format = str(bot)+": "+response['speak'] + "\n"
    if 'action' in response:
        outer_information_bot_format += response['action']
        outer_information_user_format = str(bot)+": "+response['action'] +"\n"
    if outer_information_bot_format == "":
        outer_information_bot_format, outer_information_user_format = "A small amount of time goes by."
    return inner_dialog, outer_information_bot_format, outer_information_user_format
         
def main():
    bot_memories = initiate_bot_memories()
    bot_memories[1], response = tell_bot(bot_memories[0], "Begin role-playing")
    inner_dialog, outer_information_bot_format, outer_information_user_format = parse_response(response)

    while True:
        for bot_memory in bot_memories:
            bot_memory, response = tell_bot(bot_memory, outer_information_bot_format)
            inner_dialog, outer_information_bot_format, outer_information_user_format = parse_response(response)
            
if __name__ == "__main__":
    main()