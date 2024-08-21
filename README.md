
# Firebase Photo Gallery Manager

## Description

The Firebase Photo Gallery Manager is a web application built using FastAPI, Firestore, and Firebase Authentication. It allows users to create, manage, and share photo galleries. Users can upload images, organize them into galleries, and ensure no duplicate images exist within or across galleries. The application supports user authentication through Firebase and stores images in Google Cloud Storage.

## Features

- **User Authentication**: Secure user authentication using Firebase, with sessions managed via cookies storing the Firebase ID token.
  
- **Gallery Management**: 
  - Create, edit, and delete photo galleries.
  - Each gallery is uniquely associated with a user.

- **Image Management**: 
  - Upload images to specific galleries.
  - Automatically detect and prevent duplicate images within the same gallery and across different galleries.
  - Delete images from galleries.

- **Storage and Hashing**: 
  - Images are stored in Google Cloud Storage.
  - A unique hash is generated for each image to identify duplicates.

- **Templates and Static Files**: 
  - The application uses Jinja2 for HTML templating.
  - Static files like CSS and JavaScript are served for the frontend.

## Project Structure

```plaintext
├── main.py               # Main FastAPI application code
├── local_constants.py    # Local constants (e.g., project name, bucket name)
├── templates/
│   ├── main.html         # Main template for the homepage
│   ├── update.html       # Template for updating gallery information
│   ├── gallery.html      # Template for viewing a specific gallery
├── static/
│   ├── css/              # CSS files
│   ├── js/               # JavaScript files
└── README.md             # Project README file
```


## Usage

**Home Page:** Displays a user's galleries and their first image, if any. Users can log in or out.

**Create Gallery:** Allows users to create new galleries.

**Upload Image:** Users can upload images to their galleries. Duplicates are checked and flagged.

**Edit/Delete Gallery:** Galleries can be edited or deleted by their owners.

**View Gallery:** View images within a gallery, with duplicates highlighted.

## Dependencies

- **FastAPI:** For building the web application.
- **Jinja2:** For HTML templating.
- **google-auth, google.oauth2.id_token:** For Firebase authentication.
- **google-cloud-firestore:** For interacting with Firestore.
- **google-cloud-storage:** For storing images in Google Cloud Storage.
