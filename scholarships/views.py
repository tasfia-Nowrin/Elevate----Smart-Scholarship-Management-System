from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            # check user exists
            cursor.execute("""
                SELECT user_id FROM user
                WHERE email = %s AND password = %s
            """, [email, password])
            user = cursor.fetchone()

        if user:
            user_id = user[0]
            # check if admin
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT admin_id FROM admin
                    WHERE admin_id = %s
                """, [user_id])
                admin = cursor.fetchone()

            request.session['user_id'] = user_id
            if admin:
                request.session['role'] = 'admin'
                return redirect('admin_dashboard')
            else:
                request.session['role'] = 'student'
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login')

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        university_id = request.POST.get('university_id')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # check passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        # check email not already used
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT user_id FROM user WHERE email = %s
            """, [email])
            existing = cursor.fetchone()

        if existing:
            messages.error(request, 'Email already registered')
            return redirect('register')

        # insert into user table first
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user (email, password)
                VALUES (%s, %s)
            """, [email, password])
            user_id = cursor.lastrowid

        # insert into student table
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO student (student_id, university_id, name)
                VALUES (%s, %s, %s)
            """, [user_id, university_id, name])

        messages.success(request, 'Account created! Please login.')
        return redirect('login')

    return render(request, 'register.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def student_dashboard(request):
    if request.session.get('role') != 'student':
        return redirect('login')
    return render(request, 'student_dashboard.html')


def admin_dashboard(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    return render(request, 'admin_dashboard.html')
