import anthropic, os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
history = []

while True:
    q = input("Ban: ")
    history.append({"role": "user", "content": q})
    r = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=2048,
        messages=history,
    )
    text = "".join(b.text for b in r.content if b.type == "text")
    print("Claude:", text)
    history.append({"role": "assistant", "content": text})