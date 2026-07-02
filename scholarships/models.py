# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Admin(models.Model):
    admin = models.OneToOneField('User', models.DO_NOTHING, primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'admin'


class Application(models.Model):
    application_id = models.AutoField(primary_key=True)
    application_status = models.CharField(max_length=30, blank=True, null=True)
    eligibility_result = models.CharField(max_length=30, blank=True, null=True)
    applied_date = models.DateField(blank=True, null=True)
    decision_date = models.DateField(blank=True, null=True)
    approved_waiver = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    student = models.ForeignKey('Student', models.DO_NOTHING)
    scholarship = models.ForeignKey('Scholarship', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'application'
        unique_together = (('student', 'scholarship'),)


class Deadline(models.Model):
    deadline_id = models.AutoField(primary_key=True)
    scholarship = models.OneToOneField('Scholarship', models.DO_NOTHING)
    start_date = models.DateField()
    end_date = models.DateField()
    academic_term = models.CharField(max_length=50, blank=True, null=True)
    late_application_allowed = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'deadline'


class Disbursement(models.Model):
    disbursement_id = models.AutoField(primary_key=True)
    application = models.OneToOneField(Application, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    disbursement_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'disbursement'


class Document(models.Model):
    document_id = models.AutoField(primary_key=True)
    document_type = models.CharField(max_length=50, blank=True, null=True)
    file_path = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.IntegerField(blank=True, null=True)
    application = models.ForeignKey(Application, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'document'


class Scholarship(models.Model):
    scholarship_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    fee_type = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, blank=True, null=True)
    min_cgpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    max_cgpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    waiver_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    required_ssc_gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    required_hsc_gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    no_optional_subjects = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scholarship'


class Student(models.Model):
    student = models.OneToOneField('User', models.DO_NOTHING, primary_key=True)
    university_id = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    current_semester = models.CharField(max_length=20, blank=True, null=True)
    cgpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    sibling_studies_here = models.IntegerField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'student'


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'user'

class SavedScholarship(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'scholarship')

    def __str__(self):
        return f"{self.student} - {self.scholarship}"
      