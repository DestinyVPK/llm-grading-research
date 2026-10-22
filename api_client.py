from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.environ["API_KEY"],
    base_url=os.environ["API_URL"],
    timeout=20
)

def call_model(prompt):

    # print("===== API START =====")
    try:
        response = client.chat.completions.create(
            model=os.environ["MODEL"],
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        #print("===== API END =====")

        return response.choices[0].message.content
    except Exception as e:
        print("API ERROR:",e)
        raise

