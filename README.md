# ELEVATE — Scholarship Management System 🎓

> *Where Ambition Meets Opportunity*

ELEVATE is a Django-based web application that streamlines scholarship applications, document verification, and disbursement processing for university students and administrators.

## 🌐 Live Demo

🔗 [**Visit Live Website**](https://elevate-smart-scholarship-management.onrender.com)

💻 [**View Source Code**](https://github.com/tasfia-Nowrin/Elevate----Smart-Scholarship-Management-System)

---

## Tech Stack

| Layer    | Technology                                |
| -------- | ----------------------------------------- |
| Backend  | Python 3.x, Django                        |
| Database | MySQL (raw SQL via `connection.cursor()`) |
| Frontend | HTML5, CSS3, Django Templates             |
| Auth     | Django session-based (custom role system) |


---

## Project Structure

```
ELEVATE/
│
├── database/
│   └── script.sql               # Full DB schema (run this to set up tables)
│
├── elevate/                     # Django project config
│   ├── _pycache_/
│   ├── settings.py
│   ├── urls.py
|   ├──_init_.py
│   ├── asgi.py
│   └── wsgi.py
│
├── scholarships/                # Main Django app
│   ├── _pycache_/
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── apps.py
│
├── frontend/                    # All HTML templates & CSS
│   ├── index.html
│   ├── login.html
│   ├── student_dashboard.html
│   ├── browse_scholarships.html
│   ├── application_form.html
│   ├── application_details.html
│   ├── my_applications.html
│   ├── view_applications.html
│   ├── disbursements.html
│   ├── manage_scholarships.html
│   ├── manage_deadlines.html
│   ├── manage_disbursements.html
│   ├── merit_scholarship.html
│   ├── need_based_scholars.html
│   ├── entrance_scholarship.html
│   ├── siblings_waiver.html
│   ├── admin_dashboard.html
│   ├── profile.html
│   ├── style.css                # Landing page styles
│   ├── auth.css                 # Login / Register styles
│   └── st.css                   # Student & Admin portal styles
│
├── media/
│   └── documents/               # Uploaded student documents (PDFs)
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## Database

This project uses **raw SQL** — no Django ORM models are used for business logic. All queries are executed via `django.db.connection.cursor()`.

The full schema is in **`database/script.sql`**. Run it once to create all tables.

### Entity Relationship

```
USER ──ISA──┬── STUDENT ──submits──▶ APPLICATION ──Applies_Under──▶ SCHOLARSHIP
            └── ADMIN                     │                                └──has──▶ DEADLINE
                                          ├──Includes──▶ DOCUMENT
                                          └──disbursed_as──▶ DISBURSEMENT
```

### Core Tables

| Table | Key Fields |
|---|---|
| `user` | `user_id`, `email`, `password` |
| `student` | `student_id`, `university_id`, `name`, `phone`, `department`, `current_semester`, `cgpa`, `sibling_studies_here`, `date_of_birth`, `gender`, `father_name`, `mother_name`, `tuition_fee` |
| `admin` | `admin_id`, `name` |
| `scholarship` | `scholarship_id`, `name`, `fee_type`, `description`, `status`, `min_cgpa`, `max_cgpa`, `waiver_percentage`, `required_ssc_gpa`, `required_hsc_gpa` |
| `deadline` | `deadline_id`, `scholarship_id`, `start_date`, `end_date`, `academic_term`, `is_enforced` |
| `application` | `application_id`, `student_id`, `scholarship_id`, `application_status`, `eligibility_result`, `applied_date`, `decision_date`, `approved_waiver` |
| `document` | `document_id`, `application_id`, `document_type`, `file_path`, `uploaded_at`, `is_verified` |
| `disbursement` | `disbursement_id`, `application_id`, `amount`, `disbursement_date`, `payment_method`, `payment_status`, `transaction_id` |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/tasfia-Nowrin/Elevate----Smart-Scholarship-Management-System.git
cd Elevate
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Open `elevate/settings.py` and update the `DATABASES` block:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'elevate',
        'USER': 'your_mysql_username',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 5. Create the database and run the schema

```bash
mysql -u root -p -e "CREATE DATABASE elevate;"
mysql -u root -p elevate < database/script.sql
```

### 6. Run Django's internal migrations (sessions only)

```bash
python manage.py migrate
```

### 7. Start the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`

---

## URL Routes

| URL | Page | Role |
|---|---|---|
| `/` | Landing page | Public |
| `/login/` | Login | Public |
| `/register/` | Register | Public |
| `/student/dashboard/` | Student dashboard | Student |
| `/student/browse/` | Browse scholarships | Student |
| `/student/applications/` | My applications | Student |
| `/student/profile/` | Profile | Student |
| `/portal/dashboard/` | Admin dashboard | Admin |
| `/admin/scholarships/` | Manage scholarships | Admin |
| `/admin/applications/` | View applications | Admin |
| `/admin/deadlines/` | Manage deadlines | Admin |
| `/admin/disbursements/` | Manage disbursements | Admin |

---

## User Roles

Both students and admins log in through the same `/login/` page. The system checks the `admin` table to assign the session role.

| Role | Redirected To |
|---|---|
| Student | `/student/dashboard/` |
| Admin | `/portal/dashboard/` |

---

## Scholarship Types

| Type | Criteria |
|---|---|
| Merit Scholarship | High CGPA |
| Need-Based Scholarship | Low family income / tuition support |
| Sibling Waiver | Sibling currently enrolled at the institution |
| Entrance Scholarship | High SSC / HSC GPA upon enrolment |

---

## License

For academic use only.

---

<p align="center">ELEVATE © 2026</p>
