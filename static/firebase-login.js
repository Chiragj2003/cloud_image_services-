"use strict";

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.10.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/10.10.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "",
    authDomain: "",
    projectId: "",
    storageBucket: "",
    messagingSenderId: "",
    appId: ""
};

window.addEventListener("load", function(){
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);
    document.getElementById("sign-up").addEventListener("click", function(){

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {

            const user = userCredential.user;
            console.log("User has been created");

            user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                    window.location = "/";
            });
        })
        .catch((error) => {
            console.log(error.code, error.message);
        });
    });
    document.getElementById("login").addEventListener("click", function() {
       
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {

            const user = userCredential.user;
            console.log("User has been logged in");

            user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                    window.location = "/";
            });
        })
        .catch((error) => {
            console.log(error.code, error.message);
        });
    });
    document.getElementById("sign-out").addEventListener(("click"), function() {
        signOut(auth)
        .then((output) => {
            document.cookie = "token=;path=/;SameSite=Strict";
            window.location = "/";
        })
    });
});


function updateUI (cookie) {
    var token = parseCookieToken(cookie);
    try {
        if (token.length > 0 ) {
            console.log(true)
            document.getElementById("sign-out").hidden = false;
            document.getElementById("login-box").hidden = true;
        } else {
            console.log(false)
            document.getElementById("sign-out").hidden = true;
            document.getElementById("login-box").hidden = false;
        }
    } catch (error) {
        console.log(error);
    }
}


function parseCookieToken(cookie) {
    var strings = cookie.split(";");
    for ( let i=0; i< strings.length; i++ ) {
        var temp = strings[i].split("=");
        if ( temp[0] == "token" ) {
            return temp[1];
        }
    }
    return "";
}