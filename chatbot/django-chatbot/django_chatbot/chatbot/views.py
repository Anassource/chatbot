from django.shortcuts import render, redirect
from django.http import JsonResponse
import google.generativeai as genai
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat

from django.utils import timezone


# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def ask_gemini(message):
    try:
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Create your views here.
@login_required(login_url='login')
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_gemini(message)

        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats': chats})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            if not all([username, email, password1, password2]):
                error_message = 'All fields are required'
                return render(request, 'register.html', {'error_message': error_message})

            if password1 != password2:
                error_message = 'Passwords do not match'
                return render(request, 'register.html', {'error_message': error_message})

            if User.objects.filter(username=username).exists():
                error_message = 'Username already exists'
                return render(request, 'register.html', {'error_message': error_message})

            if User.objects.filter(email=email).exists():
                error_message = 'Email already registered'
                return render(request, 'register.html', {'error_message': error_message})

            user = User.objects.create_user(username, email, password1)
            user.save()
            auth.login(request, user)
            return redirect('chatbot')

        except Exception as e:
            error_message = f'Error creating account: {str(e)}'
            return render(request, 'register.html', {'error_message': error_message})

    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')
