from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import json
import base64

url = "https://apps.beam.cloud/e928s"
headers = {
  "Accept": "*/*",
  "Accept-Encoding": "gzip, deflate",
  "Authorization": "Basic NjU1M2Y0MTQzZGI2ZTJiOGY5ZmI3ZmI4NDE5OThlMzE6ODZlOWFlYmZmNTFhOWRlMDdjOGEzNTk2NjljMmIzODY=",
  "Connection": "keep-alive",
  "Content-Type": "application/json"
}

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.post('/webhook/call')
async def webhook(request: Request):
    print('ICI', request)

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        data = json.loads(data)
        if 'payload' in data:
            audio_data = base64.b64decode(data['payload'])
            print(type(audio_data))
            # Maintenant, `audio_data` contient l'audio brut que vous pouvez passer à votre fonction de transcription
            # transcription = your_transcription_function(audio_data)

@app.post('/webhook/whatsapp')
async def webhook(request: Request):
    print('ICI', request)

    form_data = await request.form()
    message_received = form_data.get('Body')
    num_media = int(form_data.get('NumMedia', 0))

    response = MessagingResponse()

    if message_received:
        print(f"Message reçu : {message_received}")
        response.message("Hello, World!")

    if num_media > 0:
        for i in range(num_media):
            media_url = form_data.get(f'MediaUrl{i}')
            media_type = form_data.get(f'MediaContentType{i}')

            if media_type.startswith("audio/"):
                print(f"Audio reçu : {media_url}")
                payload = {"url": f"{media_url}"}
                response_beam = requests.request("POST", url, headers=headers, data=json.dumps(payload))
                print(response_beam.content)
                # Supposons que 'response_beam' est un objet 'Response' de la bibliothèque 'requests'
                response_data = json.loads(response_beam.content)  # Convertissez le contenu JSON en dictionnaire Python
                #print(response_data)  # Accédez à l'attribut 'pred' du dictionnaire
                if 'pred' in response_data:
                    print(response_data['pred'])
                    response.message(f"{response_data['pred']}")
                else:
                    response.message("")
            elif media_type.startswith("image/"):
                print(f"Image reçue : {media_url}")
                response.message("Vous avez envoyé une image.")
            elif media_type.startswith("video/"):
                print(f"Vidéo reçue : {media_url}")
                response.message("Vous avez envoyé une vidéo.")
            else:
                print(f"Type de média non pris en charge : {media_type}")

    return Response(content=str(response), media_type="application/xml")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
