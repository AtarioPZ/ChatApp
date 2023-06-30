from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import CreatedUser
from django.contrib.auth import authenticate, login

# Create your views here.
def home(request):
    is_logged_in = request.session.get('is_logged_in', False)
    return render(request, 'home.html', {'is_logged_in': is_logged_in})

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
    
    #return render(request, 'profile.html', {'user': request.user})

def my_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

