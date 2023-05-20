from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Gather
import requests
import json
import base64
from pydantic import BaseModel

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

class StreamData(BaseModel):
    event: str
    start: dict = None
    media: dict = None

@app.post("/webhook/voice")
def answer_call():
    print(1)
    response = VoiceResponse()
    print(2)
    #gather = Gather(input='dtmf', num_digits=4)
    #gather.say('Please enter the 4 digit code on your screen to get started.')
    #response.append(gather)
    print(3)
    response.say("Bienvenue, je suis en train d'écouter et de transcrire ce que vous dites.", voice='alice')
    response.say("Hello world. Bonjour, bienvenue Benjamin.", voice='alice')
    print(4)
    #response.play('https://demo.twilio.com/docs/classic.mp3')
    print(5)
    # Use <Record> to record the caller's message
    response.record()
    print(6)
    start = Start()
    start.stream(url='wss://apis-as-phere-s-team.vercel.app/stream')
    response.append(start)
    print(7)
    # End the call with <Hangup>
    #response.hangup()
    print(8)
    # Créer une instance de `Response` avec le type de contenu correct
    xml_response = Response(content=str(response), media_type="application/xml")
    print(xml_response)
    return xml_response

@app.get("/webhook/voice")
def record():
    answer_call()

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    print(11)
    await websocket.accept()
    print(12)
    while True:
        print(13)
        data = await websocket.receive_json()
        stream_data = StreamData(**data)
        print(14)
        if stream_data.media:
            print(15)
            audio_data = base64.b64decode(stream_data.media['payload'])
            print(type(audio_data))
            # Maintenant, `audio_data` contient l'audio brut que vous pouvez passer à votre fonction de transcription
            # transcription = your_transcription_function(audio_data)
            # TODO: Générer une réponse vocale en temps réel (ceci n'est pas pris en charge par Twilio au moment de l'écriture)

'''
        data = await websocket.receive_text()
        data = json.loads(data)
        if 'payload' in data:
            audio_data = base64.b64decode(data['payload'])
            print(type(audio_data))
'''

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
