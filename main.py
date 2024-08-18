from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.auth
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status
from datetime import datetime


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templets = Jinja2Templates(directory="templates")

firestore_db = firestore.Client()
firebase_request_adapter = requests.Request()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse(
            "main.html",
            {
                "request": request,
                "user_token": None,
            },
        )

    createUser(user_token)

    galleries = (
        firestore_db.collection("galleries")
        .where("userId", "==", user_token["user_id"])
        .get()
    )

    return templets.TemplateResponse(
        "main.html",
        {   "request": request,
            "user_token": user_token,
            "galleries": galleries
        }
    )


def validateFirebaseToken(id_token):
    if not id_token:
        return None
    user_token = None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter
        )
    except ValueError as err:
        print(str(err))
    return user_token


def createUser(user_token):
    user = firestore_db.collection("users").document(user_token["user_id"]).get()
    if not user.exists:
        firestore_db.collection("users").document(user_token["user_id"]).create(
            {
                "id": user_token["user_id"],
                "email": user_token["email"],
            }
        )
        user = firestore_db.collection("users").document(user_token["user_id"]).get()
    return user


@app.post("/create-gallery", response_class=HTMLResponse)
async def createGalleryHandler(req: Request):

    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse("/")

    form = await req.form()
    galleries = (
        firestore_db.collection("galleries")
        .where("userId", "==", user_token["user_id"])
        .get()
    )

    for gallery in galleries:
        if gallery.get("name") == form["name"]:
            return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    firestore_db.collection("galleries").document().set(
        {
            "name": form["name"],
            "userId": user_token["user_id"],
            "access": [],
            "created": datetime.now(),
        }
    )

    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@app.get("/gallery/edit/{galleryId}", response_class=HTMLResponse)
async def editGallery(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId).get()
    if not gallery.exists or gallery.get('userId') != user_token['user_id']:
        return RedirectResponse("/")
    
    return templets.TemplateResponse('update.html', { 'request' : req, 'user_token': user_token, "gallery": gallery })


@app.post("/gallery/edit/{galleryId}", response_class=HTMLResponse)
async def editGallery(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId)
    if not gallery.get().exists or gallery.get().get('userId') != user_token['user_id']:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    galleries = (
        firestore_db.collection("galleries")
        .where("userId", "==", user_token["user_id"])
        .get()
    )

    form = await req.form()

    for ref in galleries:
        if ref.id != gallery.id and form['name'] == ref.get('name'):
            return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
        
    gallery.update({ "name": form['name']})    
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@app.get("/gallery/delete/{galleryId}", response_class=RedirectResponse)
async def deleteGallery(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId)
    if not gallery.get().exists or gallery.get().get('userId') != user_token['user_id']:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    
    gallery.delete()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@app.get("/gallery/{galleryId}", response_class=RedirectResponse)
async def gallery(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId)
    if not gallery.get().exists or gallery.get().get('userId') != user_token['user_id']:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    
    return templets.TemplateResponse('gallery.html', { 'request' : req, 'user_token': user_token, "gallery": gallery.get() })
    