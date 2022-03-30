from multiprocessing.sharedctypes import Value
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
import random
from django.core.mail import send_mail
from cryptography.fernet import Fernet
from mechanize import Browser
import favicon
from .models import Password
from django.shortcuts import HttpResponse

br = Browser()
br.set_handle_robots(False)
fernet = Fernet(settings.KEY.encode())


def home(request):
    
    if request.method == "POST":
        
        if "registrierung-form" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            #Falls das Kennwort nicht gleich ist
            if password != password2:
                msg = "Bitte stellen Sie sicher, dass Sie dasselbe Passwort verwenden!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            #Falls Benutzername existiert
            elif User.objects.filter(username=username).exists():
                msg = f"{username} bereit existiert"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            #Falls Email existiert
            elif User.objects.filter(email=email).exists():
                msg = f"{email} bereit existiert!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                User.objects.create_user(username, email, password)
                new_user = authenticate(request, username=username, password=password2)
                if new_user is not None:
                    login(request, new_user)
                    msg = f"{username}. Vielen Danke."
                    messages.success(request, msg)
                    return HttpResponseRedirect(request.path)
        elif "Abmelden" in request.POST:
            msg = f"{request.user}. Sie haben sich abgemeldet."
            logout(request)
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif 'anmeldung-form' in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")
            new_login = authenticate(request, username=username, password=password)
            if new_login is None:
                msg = f"Login fehlgeschlagen! Stellen Sie sicher, dass Sie das richtige Konto verwenden."
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                code = str(random.randint(100000, 999999))
                global global_code
                global_code = code
                send_mail(
                    "Django Password Manager: E-Mail bestätigen",
                    f"Ihr Verifizierungscode lautet {code}.",
                    settings.EMAIL_HOST_USER,
                    [new_login.email],
                    fail_silently=False,
                )
                return render(request, "home.html", {
                    "code":code, 
                    "user":new_login,
                })

        elif "Bestätigen" in request.POST:
            input_code = request.POST.get("code")
            user = request.POST.get("user")
            if input_code != global_code:
                msg = f"{input_code} ist falsch!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                login(request, User.objects.get(username=user))
                msg = f"{request.user} herzlich Willkommen."
                messages.success(request, msg)
                return HttpResponseRedirect(request.path)
        
        elif "kennwort-hinzufügen" in request.POST:
            url = request.POST.get("url")
            email = request.POST.get("email")
            password = request.POST.get("password")
            #Daten verschlüsseln
            encrypted_email = fernet.encrypt(email.encode())
            encrypted_password = fernet.encrypt(password.encode())
            #Titel der Website abrufen
            try:
                br.open(url)
                title = br.title()
            except:
                title = url
            #Abrufen der URL des Logos
            try:
                icon = favicon.get(url)[0].url
            except:
                icon = "https://cdn-icons-png.flaticon.com/128/1006/1006771.png"
            #Speicherung die Daten in der Datenbank
            new_password = Password.objects.create(
                user=request.user,
                name=title,
                logo=icon,
                email=encrypted_email.decode(),
                password=encrypted_password.decode(),
            )
            msg = f"{title} erfolgreich hinzugefügt."
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif "löschen" in request.POST:
            to_delete = request.POST.get("password-id")
            msg = f"{Password.objects.get(id=to_delete).name} gelöscht."
            Password.objects.get(id=to_delete).delete()
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)
        
        
    
 
    context = {}
    if request.user.is_authenticated:
        passwords = Password.objects.all().filter(user=request.user)
        for password in passwords:
            password.email = fernet.decrypt(password.email.encode()).decode()
            password.password = fernet.decrypt(password.password.encode()).decode()
        context = {
            "passwords":passwords,
        } 
        

    return render(request, "home.html", context)

def kennword(request):
    characters = list('abcdefghijklmnopqrstuvwxyz')
    
    
    
    if request.GET.get('großbuchstaben'):
        characters.extend(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        
    if request.GET.get('sonderzeichen'):
        characters.extend(list('!§$&/()=?\#-_.:,;<@>|'))
    
    if request.GET.get('zahlen'):
        characters.extend(list('0123456789'))
        
    lange = int(request.GET.get('lange'))     
    thepassword = ''
    
    for x in range(lange):
        thepassword +=random.choice(characters)
        
            
    return render(request, 'kennword.html', {'kennword':thepassword})

