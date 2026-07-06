import os
import base64
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.environ.get("GROQ_API_KEY")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

all_text = ""

for i in range(9):
    img_path = f"pdf_page_{i}.png"
    base64_image = encode_image(img_path)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.2-90b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all the text from this image exactly as it appears. This is a page from an SEO audit report. Format it nicely as markdown."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1
    }
    
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", headers=headers, data=json.dumps(data).encode("utf-8"))
    
    try:
        print(f"Processing page {i}...")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            extracted = result['choices'][0]['message']['content']
            all_text += f"\n\n### Page {i+1}\n\n" + extracted
            print(f"Page {i} done.")
    except Exception as e:
        print(f"Error on page {i}: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())

with open("seoptimer_report.md", "w", encoding="utf-8") as f:
    f.write(all_text)

print("Done. Saved to seoptimer_report.md")
