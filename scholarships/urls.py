from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.index, name='index'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # =========================
    # Student
    # =========================
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/browse/', views.browse_scholarships, name='browse_scholarships'),

    # Scholarship Details
    path(
        'student/scholarship/<int:scholarship_id>/',
        views.scholarship_detail,
        name='scholarship_detail'
    ),

    # Scholarship Application Form
    path(
        'student/application/<int:scholarship_id>/',
        views.application_form,
        name='application_form'
    ),

    # Student Application Details
    path(
        'student/application/<int:application_id>/',
        views.student_application_details,
        name='student_application_details'
    ),

    # My Applications
    path(
        'student/applications/',
        views.my_applications,
        name='my_applications'
    ),

    # Profile
    path(
        'student/profile/',
        views.profile,
        name='profile'
    ),

    path(
        'student/profile/update/',
        views.profile,
        name='profile_update'
    ),

    # Save Scholarship
    path(
        'student/save/<int:scholarship_id>/',
        views.save_scholarship,
        name='save_scholarship'
    ),

    # Disbursements
    path(
        'student/disbursements/',
        views.disbursements,
        name='disbursements'
    ),

    # =========================
    # Admin
    # =========================
    path(
        'portal/dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'admin/applications/',
        views.view_applications,
        name='view_applications'
    ),

    path(
        'admin/applications/<int:app_id>/',
        views.application_details,
        name='admin_application_details'
    ),

    path(
        'admin/applications/<int:app_id>/decide/',
        views.application_decide,
        name='application_decide'
    ),

    path(
        'admin/scholarships/',
        views.manage_scholarships,
        name='manage_scholarships'
    ),

    path(
        'admin/scholarships/delete/<int:scholarship_id>/',
        views.delete_scholarship,
        name='delete_scholarship'
    ),

    path(
        'admin/deadlines/',
        views.manage_deadlines,
        name='manage_deadlines'
    ),

    path(
        'admin/deadlines/delete/<int:deadline_id>/',
        views.delete_deadline,
        name='delete_deadline'
    ),

    path(
        'admin/disbursements/',
        views.manage_disbursements,
        name='manage_disbursements'
    ),

    path(
        'admin/disbursements/create/',
        views.create_disbursement,
        name='create_disbursement'
    ),

    path(
        'admin/disbursements/update/',
        views.update_disbursement,
        name='update_disbursement'
    ),
]