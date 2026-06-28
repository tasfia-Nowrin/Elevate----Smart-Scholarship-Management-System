from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection

def index(request):
    return redirect('login')

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

    student_id = request.session.get('user_id')

    # student info
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, university_id, department, current_semester, cgpa
            FROM student WHERE student_id = %s
        """, [student_id])
        row = cursor.fetchone()
        student = {
            'name': row[0],
            'university_id': row[1],
            'department': row[2],
            'current_semester': row[3],
            'cgpa': row[4],
        }

    # stats
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM application WHERE student_id = %s
        """, [student_id])
        total_applications = cursor.fetchone()[0]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM application
            WHERE student_id = %s AND application_status = 'Pending'
        """, [student_id])
        pending_count = cursor.fetchone()[0]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM scholarship WHERE status = 'Active'
        """)
        available_scholarships = cursor.fetchone()[0]

    # next deadline
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT MIN(d.end_date)
            FROM deadline d
            JOIN scholarship s ON d.scholarship_id = s.scholarship_id
            WHERE s.status = 'Active' AND d.end_date >= CURDATE()
        """)
        result = cursor.fetchone()[0]
        next_deadline = result.strftime('%d %b') if result else 'N/A'

    # latest scholarships
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, description, waiver_percentage
            FROM scholarship
            WHERE status = 'Active'
            ORDER BY scholarship_id DESC
            LIMIT 5
        """)
        cols = [col[0] for col in cursor.description]
        latest_scholarships = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # upcoming deadlines
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.name AS scholarship_name,
                   d.end_date,
                   DATEDIFF(d.end_date, CURDATE()) AS days_remaining
            FROM deadline d
            JOIN scholarship s ON d.scholarship_id = s.scholarship_id
            WHERE s.status = 'Active'
              AND d.end_date >= CURDATE()
            ORDER BY d.end_date ASC
            LIMIT 4
        """)
        cols = [col[0] for col in cursor.description]
        upcoming_deadlines = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # my applications
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.name AS scholarship_name,
                   a.applied_date,
                   a.application_status
            FROM application a
            JOIN scholarship s ON a.scholarship_id = s.scholarship_id
            WHERE a.student_id = %s
            ORDER BY a.applied_date DESC
            LIMIT 5
        """, [student_id])
        cols = [col[0] for col in cursor.description]
        my_applications = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'student_dashboard.html', {
        'student': student,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'available_scholarships': available_scholarships,
        'next_deadline': next_deadline,
        'latest_scholarships': latest_scholarships,
        'upcoming_deadlines': upcoming_deadlines,
        'my_applications': my_applications,
    })
def browse_scholarships(request):
    if request.session.get('role') != 'student':
        return redirect('login')
    return render(request, 'browse_scholarships.html')

def my_applications(request):
    if request.session.get('role') != 'student':
        return redirect('login')
    return render(request, 'my_applications.html')

def profile(request):
    if request.session.get('role') != 'student':
        return redirect('login')
    return render(request, 'profile.html')

def manage_scholarships(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    return render(request, 'manage_scholarships.html')

def view_applications(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.application_id, st.name, st.university_id,
                   sc.name AS scholarship_name, a.applied_date, a.application_status
            FROM application a
            JOIN student     st ON a.student_id     = st.student_id
            JOIN scholarship sc ON a.scholarship_id = sc.scholarship_id
            ORDER BY a.applied_date DESC
        """)
        cols = [col[0] for col in cursor.description]
        applications = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'view_applications.html', {'applications': applications})


def application_details(request, app_id):
    if request.session.get('role') != 'admin':
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                a.application_id,
                a.application_status,
                a.applied_date,
                a.decision_date,
                sc.name              AS scholarship_name,
                d.academic_term,
                st.university_id,
                st.name              AS student_name,
                st.date_of_birth,
                st.gender,
                u.email,
                st.phone,
                st.department,
                st.current_semester,
                st.cgpa,
                st.sibling_studies_here
            FROM application a
            JOIN student     st ON a.student_id     = st.student_id
            JOIN scholarship sc ON a.scholarship_id = sc.scholarship_id
            JOIN user         u ON st.student_id    = u.user_id
            LEFT JOIN deadline d ON d.scholarship_id = sc.scholarship_id
            WHERE a.application_id = %s
        """, [app_id])
        row = cursor.fetchone()

    if not row:
        return redirect('view_applications')

    app = {
        'application_id':     row[0],
        'application_status': row[1],
        'applied_date':       row[2],
        'decision_date':      row[3],
        'scholarship_name':   row[4],
        'academic_term':      row[5] or 'N/A',
        'university_id':      row[6],
        'student_name':       row[7],
        'date_of_birth':      row[8].strftime('%d/%m/%Y') if row[8] else 'N/A',
        'gender':             row[9] or 'N/A',
        'email':              row[10],
        'phone':              row[11] or 'N/A',
        'department':         row[12] or 'N/A',
        'current_semester':   row[13] or 'N/A',
        'cgpa':               str(row[14]) + ' / 4.00' if row[14] else 'N/A',
        'sibling':            'Yes' if row[15] else 'No',
    }

    return render(request, 'application_details.html', {'app': app})


def application_decide(request, app_id):
    if request.session.get('role') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        decision = request.POST.get('decision')
        if decision in ('Approved', 'Rejected'):
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE application
                    SET application_status = %s,
                        decision_date = CURDATE()
                    WHERE application_id = %s
                """, [decision, app_id])

            if decision == 'Approved':
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO disbursement (application_id, amount, disbursement_date, payment_status)
                        SELECT %s, s.waiver_percentage, NULL, 'Pending'
                        FROM application a
                        JOIN scholarship s ON a.scholarship_id = s.scholarship_id
                        WHERE a.application_id = %s
                          AND NOT EXISTS (
                              SELECT 1 FROM disbursement WHERE application_id = %s
                          )
                    """, [app_id, app_id, app_id])

    return redirect('application_details', app_id=app_id)

def manage_deadlines(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    return render(request, 'manage_deadlines.html')


def admin_dashboard(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM scholarship WHERE status='Active')                                AS active_scholarships,
                (SELECT COUNT(*) FROM application WHERE application_status='Pending')                   AS pending_count,
                (SELECT COUNT(*) FROM application)                                                      AS total_applications,
                (SELECT IFNULL(SUM(amount),0) FROM disbursement WHERE payment_status='Paid')            AS total_disbursed
        """)
        row = cursor.fetchone()
        stats = {
            'active_scholarships': row[0],
            'pending_count':       row[1],
            'total_applications':  row[2],
            'total_disbursed':     row[3],
        }

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                st.name              AS student_name,
                sc.name              AS scholarship_name,
                a.applied_date,
                a.application_status
            FROM application a
            JOIN student     st ON a.student_id     = st.student_id
            JOIN scholarship sc ON a.scholarship_id = sc.scholarship_id
            ORDER BY a.applied_date DESC
            LIMIT 5
        """)
        cols = [col[0] for col in cursor.description]
        recent_applications = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'admin_dashboard.html', {
        **stats,
        'recent_applications': recent_applications,
    })
def manage_disbursements(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                (SELECT IFNULL(SUM(amount),0) FROM disbursement WHERE payment_status='Paid') AS total_disbursed,
                (SELECT COUNT(DISTINCT a.student_id) FROM disbursement d JOIN application a ON d.application_id=a.application_id WHERE d.payment_status='Paid') AS total_recipients,
                (SELECT COUNT(*) FROM application a LEFT JOIN disbursement d ON d.application_id=a.application_id WHERE a.application_status='Approved' AND d.disbursement_id IS NULL) AS pending_payments
        """)
        row = cursor.fetchone()
        stats = {
            'total_disbursed': row[0],
            'total_recipients': row[1],
            'pending_payments': row[2],
        }

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.disbursement_id, st.university_id, st.name AS student_name,
                   sc.name AS scholarship_name, d.amount,
                   d.disbursement_date, d.payment_status
            FROM disbursement d
            JOIN application a  ON d.application_id = a.application_id
            JOIN student     st ON a.student_id      = st.student_id
            JOIN scholarship sc ON a.scholarship_id  = sc.scholarship_id
            ORDER BY d.disbursement_date DESC
        """)
        cols = [col[0] for col in cursor.description]
        disbursements = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'manage_disbursements.html', {
        **stats,
        'disbursements': disbursements,
    })


def update_disbursement(request):
    if request.method == 'POST':
        disbursement_id = request.POST.get('disbursement_id')
        payment_status = request.POST.get('payment_status')
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE disbursement
                SET payment_status = %s
                WHERE disbursement_id = %s
            """, [payment_status, disbursement_id])
    return redirect('manage_disbursements')


def create_disbursement(request):
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        amount = request.POST.get('amount')
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO disbursement (application_id, amount, disbursement_date, payment_status)
                VALUES (%s, %s, CURDATE(), 'Paid')
            """, [application_id, amount])
    return redirect('admin_dashboard')