import requests

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