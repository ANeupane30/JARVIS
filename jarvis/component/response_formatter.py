

def complete_json_response(data):
    while True:
        try:
            for output in data['output']:
                if output['type'] == 'message':
                    for item in output['content']:
                        return item['text']
        except:
            break
        

# test = complete_json_response(data)
# print(test)