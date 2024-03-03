from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse, Start, Connect, Stream, Gather
import requests
import json
import base64
from pydantic import BaseModel
import boto3
from botocore.exceptions import NoCredentialsError

url_api = "https://apps.beam.cloud/e928s"
url_webhook = "wss://incubo.serveo.net" #"wss://twilio-asphere.herokuapp.com"
headers = {
  "Accept": "*/*",
  "Accept-Encoding": "gzip, deflate",
  "Authorization": "Basic NjU1M2Y0MTQzZGI2ZTJiOGY5ZmI3ZmI4NDE5OThlMzE6ODZlOWFlYmZmNTFhOWRlMDdjOGEzNTk2NjljMmIzODY=",
  "Connection": "keep-alive",
  "Content-Type": "application/json"
}

# AWS Credentials - Ils doivent être stockés de manière sécurisée
aws_access_key_id = 'AKIA5ZNQFWXGBYOQAJNX'
aws_secret_access_key = 'dy6aw3RAqXmbuZD9yB2YVPjKmL/VTU/ExSeCehF4'
#aws_session_token = 'your_session_token'  # facultatif
s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key)#,
                         #aws_session_token=aws_session_token)
bucket_name = 'api-beam'
parent_folder = 'twilio'

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
async def answer_call(request: Request):
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    print(call_sid)
    # Créer un dossier dans S3
    folder_name = f"{parent_folder}/{call_sid}/"
    s3_client.put_object(Bucket=bucket_name, Key=(folder_name))
    response = VoiceResponse()
    #gather = Gather(input='dtmf', num_digits=4)
    #gather.say('Please enter the 4 digit code on your screen to get started.')
    #response.append(gather)
    #response.say("Bienvenue, je suis en train d'écouter et de transcrire ce que vous dites.", voice='alice')
    response.say("Hello world. Bonjour, bienvenue Benjamin.", voice='alice')
    #response.play('https://demo.twilio.com/docs/classic.mp3')
    start = Connect()#Start()
    start.stream(url=url_webhook)
    response.append(start)
    # Use <Record> to record the caller's message
    #response.record()
    # End the call with <Hangup>
    #response.hangup()
    # Créer une instance de `Response` avec le type de contenu correct
    print(str(response))
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
            
            if media_type.startswith("audio/"):
                msg.body("Voici l'audio que vous avez envoyé :")
                msg.media(media_url)
            elif media_type.startswith("image/"):
                msg.body("Voici l'image que vous avez envoyée :")
                msg.media(media_url)
            elif media_type.startswith("video/"):
                msg.body("Voici la vidéo que vous avez envoyée :")
                msg.media(media_url)
            else:
                response.message("Type de média non pris en charge.")

    return Response(content=str(response), media_type="application/xml")

@app.post('/webhook/whatsapp')
async def webhook(request: Request):
    print('ICI', request)

    form_data = await request.form()
    sender_number = form_data.get('From')  # Récupère le numéro de téléphone de l'expéditeur
    message_received = form_data.get('Body')
    num_media = int(form_data.get('NumMedia', 0))

    response = MessagingResponse()

    # Créer un message avec un média attaché
    msg = response.message()
    if message_received:
        print(f"Message reçu : {message_received}")
        payload = {'user_id': sender_number, "prompt": f"{message_received}"}
        response_beam = requests.request("POST", url_api, headers=headers, data=json.dumps(payload))
        print('Réponse API', response_beam.content)
        # Supposons que 'response_beam' est un objet 'Response' de la bibliothèque 'requests'
        response_data = json.loads(response_beam.content)  # Convertissez le contenu JSON en dictionnaire Python
        #print(response_data)  # Accédez à l'attribut 'pred' du dictionnaire
        if 'text' in response_data:
            print('Réponse API text', response_data['output'])
            msg.body(f"{response_data['output']}")
        if 'image' in response_data:
            msg.media(response_data['url'])
        if 'video' in response_data:
            msg.media(response_data['url'])
        if 'audio' in response_data:
            msg.media(response_data['url'])
        #response.message("Hello, World!")

    if num_media > 0:
        images = []
        videos = []
        for i in range(num_media):
            media_url = form_data.get(f'MediaUrl{i}')
            media_type = form_data.get(f'MediaContentType{i}')

            if media_type.startswith("audio/"):
                print(f"Audio reçu : {media_url}")
                payload = {'audio': 1, "urls": [f"{media_url}"]}
                response_beam = requests.request("POST", url_api, headers=headers, data=json.dumps(payload))
                print(response_beam.content)
                # Supposons que 'response_beam' est un objet 'Response' de la bibliothèque 'requests'
                response_data = json.loads(response_beam.content)  # Convertissez le contenu JSON en dictionnaire Python
                #print(response_data)  # Accédez à l'attribut 'pred' du dictionnaire
                if 'text' in response_data:
                    print('Réponse API text', response_data['output'])
                    msg.body(f"{response_data['output']}")
                if 'image' in response_data:
                    msg.media(response_data['url'])
                if 'video' in response_data:
                    msg.media(response_data['url'])
                if 'audio' in response_data:
                    msg.media(response_data['url'])
                #else:
                    #response.message("")
            elif media_type.startswith("image/"):
                print(f"Image reçue : {media_url}")
                images.append(media_url)
                #response.message("Vous avez envoyé une image.")
            elif media_type.startswith("video/"):
                print(f"Vidéo reçue : {media_url}")
                videos.append(media_url)
                #response.message("Vous avez envoyé une vidéo.")
            else:
                print(f"Type de média non pris en charge : {media_type}")
    
    if len(images) > 0:
        payload = {'image': 1, "urls": [f"{media_url}"]}
        response_beam = requests.request("POST", url_api, headers=headers, data=json.dumps(payload))
        print(response_beam.content)
        # Supposons que 'response_beam' est un objet 'Response' de la bibliothèque 'requests'
        response_data = json.loads(response_beam.content)  # Convertissez le contenu JSON en dictionnaire Python
        print('Réponse API images', response_data)  # Accédez à l'attribut 'pred' du dictionnaire
    if len(videos) > 0:
        payload = {'video': 1, "urls": [f"{media_url}"]}
        response_beam = requests.request("POST", url_api, headers=headers, data=json.dumps(payload))
        print(response_beam.content)
        # Supposons que 'response_beam' est un objet 'Response' de la bibliothèque 'requests'
        response_data = json.loads(response_beam.content)  # Convertissez le contenu JSON en dictionnaire Python
        print('Réponse API videos', response_data)  # Accédez à l'attribut 'pred' du dictionnaire
    
    return Response(content=str(response), media_type="application/xml")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
