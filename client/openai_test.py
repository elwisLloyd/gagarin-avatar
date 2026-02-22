from openai import OpenAI

def test_openai():
    openai = OpenAI(api_key='')
    messages_history = [{"role": "user", "content": "Hello"}]
    completion = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages_history
    )
    openai_response = completion.choices[0].message.content
    print(openai_response)
    return openai_response

if __name__ == '__main__':
    test_openai()


