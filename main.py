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
    return templets.TemplateResponse(
        "main.html", {"request": request, "user_token": user_token}
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
        firestore_db.collection("gallery")
        .where("userId", "==", user_token["user_id"])
        .get()
    )

    for gallery in galleries:
        if gallery.get("name") == form["name"]:
            return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    firestore_db.collection("gallery").document().set(
        {
            "name": form["name"],
            "userId": user_token["user_id"],
            "access": [],
            "created": datetime.now(),
        }
    )
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
