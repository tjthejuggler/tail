import chatgpt_req

def case_insensitive_replace(my_string, target, replacement):
    s_lower = my_string.lower()
    target_lower = target.lower()
    
    index = 0
    result = []
    while index < len(my_string):
        pos = s_lower.find(target_lower, index)
        if pos == -1:
            break
        result.append(my_string[:pos] + replacement)
        my_string = my_string[pos + len(target):]
        s_lower = s_lower[pos + len(target):]
        index = pos + len(replacement)
    result.append(my_string)
    return ''.join(result)

def convert_to_third_person(character_name, gender, action):
    third_person_action, tokens = chatgpt_req.send_request([{"role": "user", "content":"Convert this first person sentence to a third person sentence about someone named '"+character_name+"'.  Their gender is "+gender+" It is very important that you use the exact name '"+character_name+"'.\n"+action+"\nRespond only with the third person sentence."}])
    print("convert_to_third")
    print("tokens", tokens)
    return(third_person_action, tokens)