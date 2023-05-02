from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.post('/webhook')
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
                response.message("Vous avez envoyé un fichier audio.")
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
