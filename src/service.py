import requests

from rich.console import Console
console = Console()

def call_sender_API(sender_psid: str, response: dict, access_token: str):
    request_body = {
        "recipient": {
            "id": sender_psid
        },
        "message": response
    }
    
    url = "https://graph.facebook.com/v2.6/me/messages/"
    qs = {"access_token": access_token}
    
    response = requests.post(url, params=qs, json=request_body)
    
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        console.log("[red][ERROR]:[/red] Unable to send message.")
        console.log("[red][ERROR]:[/red] Response: " + str(response.json()))
        console.log("[blue][INFO]:[/blue] Request body: " + str(request_body))
    