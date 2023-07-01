from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
import openai
from decouple import config

# Create your views here.
def home(request):
    is_logged_in = request.session.get('is_logged_in', False)
    
    if is_logged_in:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username FROM created_users WHERE username != %s", [request.session['username']])
            users_data = cursor.fetchall()

        users = []
        for user_data in users_data:
            user = {
                'id': user_data[0],
                'username': user_data[1],
            }
            users.append(user)

        return render(request, 'home.html', {'is_logged_in': is_logged_in, 'users_data': users})
    else:
        if request.method == 'POST':
            user_message = request.POST.get('message')
            bot_response = get_chatbot_response(user_message)
            chat_history = [
                {'sender': 'user', 'content': user_message},
                {'sender': 'bot', 'content': bot_response},
            ]
        else:
            chat_history = []
      
        return render(request, 'home.html', {'chat_history': chat_history})

def base(request):
    is_logged_in = request.session.get('is_logged_in', False)
    return render(request, 'base.html', {'is_logged_in': is_logged_in})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM created_users WHERE username = %s", [username])
            user_data = cursor.fetchone()

            if user_data:
                stored_password = user_data[3]
                if check_password(password, stored_password):
                    request.session['user_id'] = user_data[0]
                    request.session['username'] = user_data[1]  
                    request.session['is_logged_in'] = True                  
                    messages.success(request, 'Login success')
                    return redirect('profile')                    
                else:
                    messages.error(request, 'Incorrect password')
            else:
                messages.error(request, 'No user found')

        return redirect('user_login')

    return render(request, 'login.html', {'user': request.user})

def logout(request):
    request.session.clear()
    return redirect('home')

def signup(request):
    if request.method == 'POST':
        name = request.POST['name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        date_of_birth = request.POST['date_of_birth']

        hashed_password = make_password(password)

        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO created_users (name, username, email, password, date_of_birth) VALUES (%s, %s, %s, %s, %s)",
                           (name, username, email, hashed_password, date_of_birth))            
        messages.success(request, 'Sign up success')
        return redirect('user_login')
    
    return render(request, 'signup.html')

def profile(request):
    user_id = request.session.get('user_id')    

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM created_users WHERE id = %s", [user_id])
        user_data = cursor.fetchone()

    if user_data:
        name = user_data[4]
        username = user_data[1]
        email = user_data[2]
        date_of_birth = user_data[5]

        is_logged_in = request.session.get('is_logged_in', False)
        return render(request, 'profile.html', {'is_logged_in': is_logged_in, 'name': name, 'username': username, 'email': email, 'date_of_birth': date_of_birth})
    else:
        messages.error(request, 'User data not found.')
        return redirect('home')
    
def get_chatbot_response(message):
    openai.api_key = config('OPENAI_API_KEY')   

    # Send user message to the chatbot model and get the response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )

    # Extract and return the chatbot's reply
    return response['choices'][0]['message']['content']

def reset_session(request):
    if request.method == 'POST':
        request.session.flush()
        messages.success(request, 'Chat session has been reset.')
    return redirect('home')

def my_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

