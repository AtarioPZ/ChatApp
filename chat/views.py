from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
    return render(request, 'home.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cursor.fetchone()

            if user:
                stored_password = user[3]
                if check_password(password, stored_password):
                    messages.success(request, 'Login success')
                    return redirect('profile')
                else:
                    messages.success(request, 'Incorrect password')                    
            else:
                messages.success(request, 'No user found')            
        return redirect('user_login')

    return render(request, 'login.html')

def logout(request):
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
            cursor.execute("INSERT INTO users (name, username, email, password, date_of_birth) VALUES (%s, %s, %s, %s, %s)",
                           (name, username, email, hashed_password, date_of_birth))            
        messages.success(request, 'Sign up success')
        return redirect('login')
    
    return render(request, 'signup.html')

@login_required
def profile(request):
    user_id = request.user.id

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
        user_data = cursor.fetchone()

    if user_data:
        # Extract the relevant data from the user_data tuple
        name = user_data[1]
        username = user_data[2]
        email = user_data[3]
        date_of_birth = user_data[4]

        return render(request, 'profile.html', {'name': name, 'username': username, 'email': email, 'date_of_birth': date_of_birth})
    else:
        messages.error(request, 'User data not found.')
        return redirect('home')
    
    return render(request, 'profile.html', {'user': user})

def my_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

