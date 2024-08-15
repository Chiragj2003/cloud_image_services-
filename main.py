from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.auth
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore, storage
import starlette.status as status
from datetime import datetime
import local_constants
import hashlib

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

    images = galleryFistImage(galleries)

    return templets.TemplateResponse(
        "main.html",
        {   "request": request,
            "user_token": user_token,
            "galleries": galleries,
            "images" : images
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

    if not gallery.get().exists:
        return RedirectResponse("/")
    
    print("User", user_token['email'])
    print("Access", gallery.get().get("access" ))

    if gallery.get().get('userId') != user_token['user_id'] and  user_token['email'] not in gallery.get().get("access" ) :
        return RedirectResponse("/")
    
    images = firestore_db.collection('images').where("galleryId", "==", galleryId).get()
    duplicatesInSameGallery = []
    seen = []
    hashes = set()
    for image in images:
        hashId = image.get('hashId')
        print(hashId)
        if hashId in seen:
            duplicatesInSameGallery.append(image)
        else:
            seen.append(hashId)
        hashes.add(hashId)
    del(seen)

    userImages = firestore_db.collection('images').where('userId', "==", user_token['user_id']).get()
    duplicateImageInOtherGalleries = []
    for image in userImages:
        if image.get("galleryId")!=galleryId and image.get("hashId") in hashes:
            duplicateImageInOtherGalleries.append(image)
    
    return templets.TemplateResponse('gallery.html', { 'request' : req, 'user_token': user_token, "gallery": gallery.get(), "images" : images, "duplicatesInSameGallery": duplicatesInSameGallery, "duplicateImageInOtherGalleries" : duplicateImageInOtherGalleries })
    

def addFile (file):
    storage_client = storage.Client( project = local_constants.PROJECT_NAME )
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = storage.Blob(file.filename, bucket)
    blob.upload_from_file(file.file)
    blob.make_public()
    return blob.public_url


def hashing( file ):
    hash = hashlib.md5()
    content = file.file.read()
    hash.update(content)
    file.file.seek(0)
    return hash.hexdigest()


@app.post("/upload-image/{id}", response_class=RedirectResponse)
async def uploadImage ( req: Request, id: str ):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None , 'user_info': None })
    
    gallery = firestore_db.collection('galleries').document(id).get()
    if not gallery.exists or gallery.get('userId') != user_token['user_id']:
        return RedirectResponse("/")
    
    form = await req.form()
    hashId = hashing(form['image'])
    url = addFile( form['image'] )

    firestore_db.collection('images').document().set({
        "url" : url,
        "name" : form['image'].filename,
        "galleryId" : gallery.id,
        "userId" : user_token['user_id'],
        "created" : datetime.now(),
        "hashId" : hashId
    })
    
    return RedirectResponse(f"/gallery/{id}", status_code=status.HTTP_302_FOUND)


@app.get("/image/delete/{id}", response_class=RedirectResponse)
async def deleteImage ( req: Request, id: str ):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None , 'user_info': None })
    
    image = firestore_db.collection('images').document(id)
    if not image.get().exists or image.get().get('userId') != user_token['user_id']:
        return RedirectResponse("/")
    
    galleryId = image.get().get('galleryId')
    image.delete()
    
    return RedirectResponse(f"/gallery/{galleryId}", status_code=status.HTTP_302_FOUND)

def galleryFistImage( galleries ):
    images = {}
    for gallery in galleries:
        image = firestore_db.collection('images').where('galleryId', '==', gallery.id).order_by("created", "ASCENDING").limit(1).get()
        if len(image) != 0:
            images[gallery.id] = image[0].get('url')
    return images


@app.get("/share/{galleryId}", response_class=RedirectResponse)
async def share(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId).get()
    if not gallery.exists or gallery.get('userId') != user_token['user_id']:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    
    return templets.TemplateResponse('share.html', { 'request' : req, 'user_token': user_token, "gallery": gallery })
    


@app.post("/share/allow/{galleryId}", response_class=RedirectResponse)
async def allow(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId)
    if not gallery.get().exists or gallery.get().get('userId') != user_token['user_id']:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    
    form = await req.form()
    allowed_users = set(gallery.get().get('access'))
    
    allowed_users.add(form['email'])

    gallery.update({ "access" : allowed_users })

    return RedirectResponse(f"/share/{galleryId}", status_code=status.HTTP_302_FOUND)

@app.post("/share/disallow/{galleryId}", response_class=RedirectResponse)
async def disAllow(req: Request, galleryId:str):
    id_token = req.cookies.get("token")
    user_token = None
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return templets.TemplateResponse('main.html', { 'request' : req, 'user_token' : None })

    gallery = firestore_db.collection('galleries').document(galleryId)
    if not gallery.get().exists or gallery.get().get('userId') != user_token['user_id']:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    
    form = await req.form()
    allowed_users = set(gallery.get().get('access'))
    
    if form['email'] in allowed_users:
        allowed_users.remove(form['email'])

    gallery.update({ "access" : allowed_users })

    return RedirectResponse(f"/share/{galleryId}", status_code=status.HTTP_302_FOUND)

# Allowed
# http://127.0.0.1:8000/share/jqsEtW6zuaZIIgKuzpht

# Disallowed

# 
    