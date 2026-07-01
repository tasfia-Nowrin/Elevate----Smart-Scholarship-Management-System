from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from datetime import date
from .models import Student, Scholarship, SavedScholarship

def save_scholarship(request, scholarship_id):
    student = Student.objects.get(user=request.user)

    scholarship = get_object_or_404(
        Scholarship,
        pk=scholarship_id
    )

    SavedScholarship.objects.get_or_create(
        student=student,
        scholarship=scholarship
    )

    return redirect(request.META.get('HTTP_REFERER'))

def index(request):
    scholarships = Scholarship.objects.filter(status="Active")
    return render(request, "index.html", {
        "scholarships": scholarships
    })
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
            ORDER BY d.end_date ASC
            LIMIT 4
        """)
        cols = [col[0] for col in cursor.description]
        upcoming_deadlines = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # my applications
    # replace my_applications query with this
# my applications
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                s.name AS scholarship_name,
                a.applied_date,
                a.application_status,
                d.amount
            FROM application a
            JOIN scholarship s ON a.scholarship_id = s.scholarship_id
            LEFT JOIN disbursement d ON d.application_id = a.application_id
            WHERE a.student_id = %s
            ORDER BY a.applied_date DESC
            LIMIT 5
        """, [student_id])
        cols = [col[0] for col in cursor.description]
        my_applications = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # total received
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT IFNULL(SUM(d.amount), 0)
            FROM disbursement d
            JOIN application a ON d.application_id = a.application_id
            WHERE a.student_id = %s
              AND d.payment_status = 'Paid'
        """, [student_id])
        total_received = cursor.fetchone()[0]

    return render(request, 'student_dashboard.html', {
        'student': student,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'available_scholarships': available_scholarships,
        'next_deadline': next_deadline,
        'latest_scholarships': latest_scholarships,
        'upcoming_deadlines': upcoming_deadlines,
        'my_applications': my_applications,
        'total_received': total_received,
    })

def browse_scholarships(request):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    # get student info for eligibility check
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cgpa, sibling_studies_here
            FROM student WHERE student_id = %s
        """, [student_id])
        row = cursor.fetchone()
        student_cgpa = row[0] or 0
        has_sibling = row[1]


    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM student WHERE student_id = %s", [student_id])
        student_name = cursor.fetchone()[0]


    # get all active scholarships with deadlines
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.scholarship_id, s.name, s.description, s.waiver_percentage,
                   s.min_cgpa, s.max_cgpa, s.fee_type,
                   s.required_ssc_gpa, s.required_hsc_gpa,
                   d.end_date,
                   a.application_id, a.application_status
            FROM scholarship s
            LEFT JOIN deadline d ON d.scholarship_id = s.scholarship_id
            LEFT JOIN application a ON a.scholarship_id = s.scholarship_id
                AND a.student_id = %s
            WHERE s.status = 'Active'
            ORDER BY d.end_date ASC
        """, [student_id])
        cols = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    scholarships = []
    for row in rows:
        s = dict(zip(cols, row))

        # determine type for filter
        name_lower = s['name'].lower()
        if 'merit' in name_lower:
            s['type'] = 'merit'
        elif 'need' in name_lower:
            s['type'] = 'need'
        elif 'sibling' in name_lower:
            s['type'] = 'sibling'
        elif 'entrance' in name_lower:
            s['type'] = 'entrance'
        else:
            s['type'] = 'other'

        # eligibility check
        eligible = False
        if s['type'] == 'merit':
            eligible = student_cgpa >= (s['min_cgpa'] or 0)
        elif s['type'] == 'need':
            eligible = True  # needs manual review, mark eligible by default
        elif s['type'] == 'sibling':
            eligible = bool(has_sibling)
        elif s['type'] == 'entrance':
            eligible = True  # based on SSC/HSC, mark eligible by default

        s['eligible'] = eligible
        s['already_applied'] = s['application_id'] is not None
        s['end_date_fmt'] = s['end_date'].strftime('%d %b %Y') if s['end_date'] else 'N/A'

        scholarships.append(s)

    return render(request, 'browse_scholarships.html', {
    'scholarships': scholarships,
    'student_cgpa': student_cgpa,
    'student_name': student_name,
})

def apply_scholarship(request, scholarship_id):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    # check if already applied
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT application_id FROM application
            WHERE student_id = %s AND scholarship_id = %s
        """, [student_id, scholarship_id])
        existing = cursor.fetchone()

    if existing:
        messages.info(request, 'You have already applied to this scholarship.')
        return redirect('browse_scholarships')

    # insert new application
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO application (student_id, scholarship_id, applied_date, application_status)
            VALUES (%s, %s, CURDATE(), 'Pending')
        """, [student_id, scholarship_id])

    messages.success(request, 'Application submitted successfully!')
    return redirect('my_applications')

def disbursements(request):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM student WHERE student_id = %s", [student_id])
        student_name = cursor.fetchone()[0]

    # summary stats
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                IFNULL(SUM(d.amount), 0),
                COUNT(d.disbursement_id),
                MAX(d.disbursement_date)
            FROM disbursement d
            JOIN application a ON d.application_id = a.application_id
            WHERE a.student_id = %s AND d.payment_status = 'Paid'
        """, [student_id])
        row = cursor.fetchone()
        total_amount = row[0]
        received_count = row[1]
        last_payment = row[2].strftime('%d %b %Y') if row[2] else None

    # paid disbursements
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT sc.name, sc.fee_type, sc.waiver_percentage,
                   d.amount, d.disbursement_date, d.disbursement_id, d.payment_status
            FROM disbursement d
            JOIN application a ON d.application_id = a.application_id
            JOIN scholarship sc ON a.scholarship_id = sc.scholarship_id
            WHERE a.student_id = %s AND d.payment_status = 'Paid'
            ORDER BY d.disbursement_date DESC
        """, [student_id])
        paid = cursor.fetchall()

    # pending: approved applications with pending/no disbursement
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT sc.name, a.applied_date, sc.waiver_percentage, d.payment_status
            FROM application a
            JOIN scholarship sc ON a.scholarship_id = sc.scholarship_id
            LEFT JOIN disbursement d ON d.application_id = a.application_id
            WHERE a.student_id = %s
              AND a.application_status = 'Approved'
              AND (d.payment_status IS NULL OR d.payment_status != 'Paid')
            ORDER BY a.applied_date DESC
        """, [student_id])
        pending = cursor.fetchall()

    return render(request, 'disbursements.html', {
        'student_name': student_name,
        'total_amount': total_amount,
        'received_count': received_count,
        'last_payment': last_payment,
        'paid': paid,
        'pending': pending,
    })

    
def profile(request):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        father_name = request.POST.get('father_name')
        mother_name = request.POST.get('mother_name')
        department = request.POST.get('department')
        current_semester = request.POST.get('current_semester')
        cgpa = request.POST.get('cgpa')

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE student
                SET name=%s, phone=%s, date_of_birth=%s, gender=%s,
                    father_name=%s, mother_name=%s, department=%s,
                    current_semester=%s, cgpa=%s
                WHERE student_id=%s
            """, [name, phone, date_of_birth, gender, father_name,
                  mother_name, department, current_semester, cgpa, student_id])

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    # GET — fetch student data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.name, s.university_id, s.phone, s.department,
                   s.current_semester, s.cgpa, s.date_of_birth, s.gender,
                   s.father_name, s.mother_name, s.sibling_studies_here,
                   u.email
            FROM student s
            JOIN user u ON u.user_id = s.student_id
            WHERE s.student_id = %s
        """, [student_id])
        row = cursor.fetchone()
        student = {
            'name': row[0],
            'university_id': row[1],
            'phone': row[2],
            'department': row[3],
            'current_semester': row[4],
            'cgpa': row[5],
            'date_of_birth': row[6],
            'gender': row[7],
            'father_name': row[8],
            'mother_name': row[9],
            'sibling_studies_here': row[10],
            'email': row[11],
        }

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM application WHERE student_id = %s
        """, [student_id])
        total_applications = cursor.fetchone()[0]

    return render(request, 'profile.html', {
        'student': student,
        'total_applications': total_applications,
    })

def manage_scholarships(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    return render(request, 'manage_scholarships.html')

def view_applications(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    return render(request, 'view_applications.html')

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


def my_applications(request):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM student WHERE student_id = %s", [student_id])
        student_name = cursor.fetchone()[0]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                a.application_id,
                s.name AS scholarship_name,
                s.waiver_percentage,
                a.applied_date,
                a.application_status,
                a.decision_date,
                a.approved_waiver,
                d.amount,
                d.payment_status
            FROM application a
            JOIN scholarship s ON a.scholarship_id = s.scholarship_id
            LEFT JOIN disbursement d ON d.application_id = a.application_id
            WHERE a.student_id = %s
            ORDER BY a.applied_date DESC
        """, [student_id])
        cols = [col[0] for col in cursor.description]
        applications = [dict(zip(cols, row)) for row in cursor.fetchall()]

    for app in applications:
        app['status_lower'] = app['application_status'].lower()

    stats = {
        'total': len(applications),
        'pending': sum(1 for a in applications if a['application_status'] == 'Pending'),
        'approved': sum(1 for a in applications if a['application_status'] == 'Approved'),
        'rejected': sum(1 for a in applications if a['application_status'] == 'Rejected'),
    }

    return render(request, 'my_applications.html', {
        'student_name': student_name,
        'applications': applications,
        'stats': stats,
    })


def scholarship_detail(request, scholarship_id):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("""SELECT name FROM student WHERE student_id = %s""", [student_id])

        row = cursor.fetchone()
        student_name = row[0] if row else "Student"

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.scholarship_id, s.name, s.description, s.waiver_percentage,
                   s.min_cgpa, s.max_cgpa, s.fee_type,
                   s.required_ssc_gpa, s.required_hsc_gpa,
                   d.end_date,
                   a.application_id, a.application_status
            FROM scholarship s
            LEFT JOIN deadline d ON d.scholarship_id = s.scholarship_id
            LEFT JOIN application a ON a.scholarship_id = s.scholarship_id
                AND a.student_id = %s
            WHERE s.scholarship_id = %s
        """, [student_id, scholarship_id])
        cols = [col[0] for col in cursor.description]
        row = cursor.fetchone()

    if not row:
        messages.error(request, 'Scholarship not found.')
        return redirect('browse_scholarships')

    sch = dict(zip(cols, row))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cgpa, sibling_studies_here FROM student WHERE student_id = %s
        """, [student_id])
        srow = cursor.fetchone()
        student_cgpa = srow[0] or 0
        has_sibling = srow[1]

    name_lower = sch['name'].lower()
    if 'merit' in name_lower:
        sch['type'], sch['type_label'] = 'merit', 'Merit-Based'
    elif 'need' in name_lower:
        sch['type'], sch['type_label'] = 'need', 'Need-Based'
    elif 'sibling' in name_lower:
        sch['type'], sch['type_label'] = 'sibling', 'Sibling Waiver'
    elif 'entrance' in name_lower:
        sch['type'], sch['type_label'] = 'entrance', 'Entrance'
    else:
        sch['type'], sch['type_label'] = 'other', sch['name']

    if sch['type'] == 'merit':
        eligible = student_cgpa >= (sch['min_cgpa'] or 0)
    elif sch['type'] == 'sibling':
        eligible = bool(has_sibling)
    else:
        eligible = True  # need / entrance: manual review, eligible by default

    sch['eligible'] = eligible
    sch['already_applied'] = sch['application_id'] is not None

    if sch['end_date']:
        days = (sch['end_date'] - date.today()).days
        sch['days_remaining'] = max(days, 0)
        sch['end_date_fmt'] = sch['end_date'].strftime('%d %B %Y')
    else:
        sch['days_remaining'] = None
        sch['end_date_fmt'] = 'N/A'

    if sch['type'] == 'merit':
        template = 'merit_scholarship.html'
    elif sch['type'] == 'need':
        template = 'need_based_scholarship.html'
    elif sch['type'] == 'sibling':
        template = 'siblings_waiver.html'
    elif sch['type'] == 'entrance':
        template = 'entrance_scholarship.html'
    else:
        template = 'scholarship_detail.html'   # fallback

    return render(request, template, {
        'student_name': student_name,
        'sch': sch,
    })


def application_details(request, application_id):
    if request.session.get('role') != 'student':
        return redirect('login')

    student_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM student WHERE student_id = %s", [student_id])
        student_name = cursor.fetchone()[0]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                a.application_id,
                a.application_status,
                a.eligibility_result,
                a.applied_date,
                a.decision_date,
                a.approved_waiver,
                s.name AS scholarship_name,
                s.waiver_percentage,
                st.name AS student_name,
                st.university_id,
                st.date_of_birth,
                st.gender,
                st.phone,
                st.department,
                st.cgpa,
                st.current_semester,
                u.email,
                d.amount,
                d.payment_status
            FROM application a
            JOIN scholarship s ON a.scholarship_id = s.scholarship_id
            JOIN student st ON a.student_id = st.student_id
            JOIN user u ON u.user_id = st.student_id
            LEFT JOIN disbursement d ON d.application_id = a.application_id
            WHERE a.application_id = %s AND a.student_id = %s
        """, [application_id, student_id])
        row = cursor.fetchone()

    if not row:
        messages.error(request, 'Application not found.')
        return redirect('my_applications')

    app = {
        'application_id': row[0],
        'application_status': row[1],
        'eligibility_result': row[2],
        'applied_date': row[3],
        'decision_date': row[4],
        'approved_waiver': row[5],
        'scholarship_name': row[6],
        'waiver_percentage': row[7],
        'student_name': row[8],
        'university_id': row[9],
        'date_of_birth': row[10],
        'gender': row[11],
        'phone': row[12],
        'department': row[13],
        'cgpa': row[14],
        'current_semester': row[15],
        'email': row[16],
        'amount': row[17],
        'payment_status': row[18],
        'status_lower': row[1].lower() if row[1] else 'pending',
    }

    return render(request, 'application_details.html', {
        'app': app,
        'student_name': student_name,
    })

def save_scholarship(request, scholarship_id):

    if 'student_id' not in request.session:
        return redirect('login')

    student = Student.objects.get(
        pk=request.session['student_id']
    )

    scholarship = Scholarship.objects.get(
        pk=scholarship_id
    )

    SavedScholarship.objects.get_or_create(
        student=student,
        scholarship=scholarship
    )

    messages.success(request, "Scholarship saved successfully.")

    return redirect(request.META.get('HTTP_REFERER',
                                     'browse_scholarships'))


def application_form(request, scholarship_id):

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM scholarship
        WHERE scholarship_id=%s
    """, [scholarship_id])

    scholarship = cursor.fetchone()

    # Get logged in student
    student = Student.objects.get(student_id=request.session["user_id"])

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        cgpa = request.POST.get("cgpa")
        income = request.POST.get("family_income")
        statement = request.POST.get("statement")

        transcript = request.FILES.get("transcript")
        nid = request.FILES.get("nid")

        cursor.execute("""
            INSERT INTO application
            (
                application_status,
                eligibility_result,
                applied_date,
                student_id,
                scholarship_id
            )
            VALUES
            (
                'Pending',
                'Under Review',
                CURDATE(),
                %s,
                %s
            )
        """, [student.student_id, scholarship_id])

        return redirect("my_applications")

    # ← THIS MUST BE OUTSIDE THE if BLOCK
    return render(request, "application_form.html", {
    "scholarship": scholarship,
    "student": student,
    "student_name": student.name,
})
                                   