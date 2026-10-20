USE elevate;

-- 1. user first 
CREATE TABLE user (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(150) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL
);

-- 2. student 
CREATE TABLE student (
    student_id INT PRIMARY KEY,
    university_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(100),
    current_semester VARCHAR(20),
    cgpa DECIMAL(3,2),
    sibling_studies_here BOOLEAN DEFAULT FALSE,
    date_of_birth DATE,
    gender VARCHAR(10),
    father_name VARCHAR(100),
    mother_name VARCHAR(100),
    tuition_fee DECIMAL(10,2),
    CONSTRAINT fk_student_user
        FOREIGN KEY (student_id) REFERENCES user(user_id)
        ON DELETE CASCADE
);

-- 3. admin 
CREATE TABLE admin (
    admin_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_admin_user
        FOREIGN KEY (admin_id) REFERENCES user(user_id)
        ON DELETE CASCADE
);

-- 4. scholarship 
CREATE TABLE scholarship (
    scholarship_id        INT AUTO_INCREMENT PRIMARY KEY,
    name                  VARCHAR(150) NOT NULL,
    fee_type              VARCHAR(50),
    description           TEXT,
    status                VARCHAR(30),
    min_cgpa              DECIMAL(3,2),
    max_cgpa              DECIMAL(3,2),
    waiver_percentage     DECIMAL(5,2),
    required_ssc_gpa      DECIMAL(3,2),
    required_hsc_gpa      DECIMAL(3,2),
    no_optional_subjects  INT
);

-- 5. deadline 
CREATE TABLE deadline (
    deadline_id     INT AUTO_INCREMENT PRIMARY KEY,
    scholarship_id  INT NOT NULL UNIQUE,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    academic_term   VARCHAR(50),
    late_application_allowed BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_deadline_scholarship
        FOREIGN KEY (scholarship_id) REFERENCES scholarship(scholarship_id)
        ON DELETE CASCADE
);

-- 6. application 
CREATE TABLE application (
    application_id       INT AUTO_INCREMENT PRIMARY KEY,
    application_status   VARCHAR(30),
    eligibility_result   VARCHAR(30),
    applied_date         DATE,
    decision_date        DATE,
    approved_waiver      DECIMAL(5,2),
    student_id           INT NOT NULL,
    scholarship_id       INT NOT NULL,
    CONSTRAINT fk_application_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_application_scholarship
        FOREIGN KEY (scholarship_id) REFERENCES scholarship(scholarship_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_student_scholarship
        UNIQUE(student_id, scholarship_id)
);

-- 7. document 
CREATE TABLE document (
    document_id      INT AUTO_INCREMENT PRIMARY KEY,
    document_type    VARCHAR(50),
    file_path        VARCHAR(255),
    uploaded_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_verified      BOOLEAN DEFAULT FALSE,
    application_id   INT NOT NULL,
    CONSTRAINT fk_document_application
        FOREIGN KEY (application_id) REFERENCES application(application_id)
        ON DELETE CASCADE
);

-- 8. disbursement 
CREATE TABLE disbursement (
    disbursement_id   INT AUTO_INCREMENT PRIMARY KEY,
    application_id    INT NOT NULL UNIQUE,
    amount            DECIMAL(10,2) NOT NULL,
    disbursement_date DATE,
    payment_status    VARCHAR(30) DEFAULT 'pending',
    CONSTRAINT fk_disbursement_application
        FOREIGN KEY (application_id) REFERENCES application(application_id)
        ON DELETE CASCADE
);

-- 9. indexes
CREATE INDEX idx_application_student    ON application(student_id);
CREATE INDEX idx_application_scholarship ON application(scholarship_id);
CREATE INDEX idx_document_application   ON document(application_id);
CREATE INDEX idx_disbursement_application ON disbursement(application_id);