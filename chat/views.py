from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
import openai
from decouple import config
from datetime import date
from django.utils import timezone
from django.http import JsonResponse

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

                    # Update last_seen in the created_users table
                    cursor.execute("UPDATE created_users SET last_seen = %s WHERE id = %s", [timezone.now(), user_data[0]])

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
        registration_date = date.today()

        hashed_password = make_password(password)

        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO created_users (name, username, email, password, date_of_birth, registration_date, online_status, account_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (name, username, email, hashed_password, date_of_birth, registration_date, True, "Online"))            
        messages.success(request, 'Sign up success')
        return redirect('user_login')
    
    return render(request, 'signup.html')

def profile(request):
    user_id = request.session.get('user_id')

    # Fetch user data
    with connection.cursor() as cursor:        
        cursor.execute("SELECT * FROM created_users WHERE id = %s", [user_id])
        user_data = cursor.fetchone()

        if user_data:
            name = user_data[4]
            username = user_data[1]
            email = user_data[2]
            date_of_birth = user_data[5]
            registration_date = user_data[11]
            online_status = user_data[10]
            account_status = user_data[18]
            last_seen = user_data[7]

            is_logged_in = request.session.get('is_logged_in', False)

            # Fetch friend data with status 'accepted'
            cursor.execute("SELECT friend_id FROM user_friends WHERE user_id = %s AND status = %s", [user_id, 'accepted'])
            friend_ids = cursor.fetchall()

            friends = []
            for friend_id in friend_ids:
                cursor.execute("SELECT * FROM created_users WHERE id = %s", [friend_id[0]])
                friend_data = cursor.fetchone()
                friends.append({
                    'id': friend_data[0],
                    'username': friend_data[1],
                    'name': friend_data[4]
                })
            
            cursor.execute("SELECT friend_id FROM user_friends WHERE user_id = %s AND status = %s", [user_id, 'pending'])
            pending_friend_ids = cursor.fetchall()

            pending_users = []
            for pending_friend_id in pending_friend_ids:
                cursor.execute("SELECT * FROM created_users WHERE id = %s", [pending_friend_id[0]])
                pending_friend_data = cursor.fetchone()
                pending_users.append({
                    'id': pending_friend_data[0],
                    'username': pending_friend_data[1],
                    'name': pending_friend_data[4]
                })

            cursor.execute("SELECT user_id FROM user_friends WHERE friend_id = %s AND status = %s", [user_id, 'pending'])
            incoming_friend_ids = cursor.fetchall()

            incoming_users = []
            for incoming_friend_id in incoming_friend_ids:
                cursor.execute("SELECT * FROM created_users WHERE id = %s", [incoming_friend_id[0]])
                incoming_friend_data = cursor.fetchone()
                incoming_users.append({
                    'id': incoming_friend_data[0],
                    'username': incoming_friend_data[1],
                    'name': incoming_friend_data[4]
                })

            if request.method == 'POST':
                friend_id = request.POST.get('friend_id')
                action = request.POST.get('action')
                friend_username = request.POST.get('friend_username', '')

                # Check if the friend username exists in the database
                cursor.execute("SELECT id FROM created_users WHERE username = %s", [friend_username])               
                friend_result = cursor.fetchone()

                if friend_result:
                    friend_id = friend_result[0]

                    if action == 'add':
                        cursor.execute("INSERT INTO user_friends (user_id, friend_id, status) VALUES (%s, %s, %s)",
                                    [user_id, friend_id, 'pending'])
                        cursor.connection.commit()
                        messages.success(request, f"Friend request sent to {friend_username}!")
                        return redirect('profile')
                    elif action == 'cancel':
                        friend_username = request.POST.get('friend_username', '')  # Retrieve friend_username from POST data
                        cursor.execute("DELETE FROM user_friends WHERE status = 'pending' AND friend_id = %s AND user_id = %s",
                                    [friend_id, user_id])
                        cursor.connection.commit()
                        messages.success(request, f"Friend request to {friend_username} cancelled successfully!")
                        return redirect('profile')

                else:
                    error_message = 'Please enter correct username (case sensitive)'             

                if friend_id and action:
                    if action == 'accept':
                        cursor.execute("UPDATE user_friends SET status = %s WHERE user_id = %s AND friend_id = %s",
                                        ['accepted', friend_id, user_id])
                        # Update the status for the user who sent the friend request
                        cursor.execute("INSERT INTO user_friends (user_id, friend_id, status) VALUES (%s, %s, %s)",
                                        [user_id, friend_id, 'accepted'])
                        cursor.connection.commit()

                    elif action == 'reject':
                        cursor.execute("DELETE FROM user_friends WHERE user_id = %s AND friend_id = %s",
                                       [friend_id, user_id])
                        cursor.connection.commit()                    

                    # Fetch friend data with updated statuses
                    cursor.execute("SELECT friend_id FROM user_friends WHERE user_id = %s AND status = %s",
                                   [user_id, 'accepted'])
                    friend_ids = cursor.fetchall()

                    friends = []
                    for friend_id in friend_ids:
                        cursor.execute("SELECT * FROM created_users WHERE id = %s", [friend_id[0]])
                        friend_data = cursor.fetchone()
                        friends.append({
                            'id': friend_data[0],
                            'username': friend_data[1],
                            'name': friend_data[4]
                        })

                    cursor.execute("SELECT friend_id FROM user_friends WHERE user_id = %s AND status = %s",
                                   [user_id, 'pending'])
                    pending_friend_ids = cursor.fetchall()

                    pending_users = []
                    for pending_friend_id in pending_friend_ids:
                        cursor.execute("SELECT * FROM created_users WHERE id = %s", [pending_friend_id[0]])
                        pending_friend_data = cursor.fetchone()
                        pending_users.append({
                            'id': pending_friend_data[0],
                            'username': pending_friend_data[1],
                            'name': pending_friend_data[4]
                        })

                    cursor.execute("SELECT user_id FROM user_friends WHERE friend_id = %s AND status = %s",
                                   [user_id, 'pending'])
                    incoming_friend_ids = cursor.fetchall()

                    incoming_users = []
                    for incoming_friend_id in incoming_friend_ids:
                        cursor.execute("SELECT * FROM created_users WHERE id = %s", [incoming_friend_id[0]])
                        incoming_friend_data = cursor.fetchone()
                        incoming_users.append({
                            'id': incoming_friend_data[0],
                            'username': incoming_friend_data[1],
                            'name': incoming_friend_data[4]
                        })

            return render(request, 'profile.html', {
                'is_logged_in': is_logged_in,
                'name': name,
                'username': username,
                'email': email,
                'date_of_birth': date_of_birth,
                'registration_date': registration_date,
                'online_status': online_status,
                'account_status': account_status,
                'last_seen': last_seen,
                'friends': friends,
                'pending_requests': pending_users,
                'incoming_requests': incoming_users,
            })

    # Handle case when user data is not found
    messages.error(request, 'User data not found.')
    return redirect('user_login')
    
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

def chatpage(request):
    is_logged_in = request.session.get('is_logged_in', False)
    return render(request, 'chatpage.html', {'is_logged_in': is_logged_in})

def my_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)
