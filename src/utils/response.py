# Copyright 2026 The Ronny Voice Foundation

model = 'moonshotai/kimi-k2-instruct-0905'
system_prompt = open("src/utils/system_prompt.txt").read()

def get_response(client, context):
    """
    Request and return a response from the Groq model once it finishes.
    
    :param client: The client for the script to connect to.
    :param context: The context for the model, including the current question.
    """
    completion = client.chat.completions.create(
        model=model,
        messages =
        [{
            'role': 'system',
            'content': system_prompt,
        }] + context, # Just add all the context passed in! Very easy :D
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content