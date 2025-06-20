# School Management System

A comprehensive school management system built with Django, featuring pupil management, QR code-based attendance tracking, assessment management, and communication tools.

## Features

### User Management
- Role-based authentication (Admin, Teacher)
- Custom user profiles with contact information

### Pupil Management
- Comprehensive pupil records (demographics, enrollment details, contact information)
- Parent/Guardian information
- Automatic QR code generation for each pupil

### Attendance Tracking
- QR code-based attendance system
- Multiple attendance sessions (morning, afternoon, etc.)
- Track different attendance statuses (present, absent, late, excused)
- Attendance reports and statistics

### Assessment Management
- Create and manage subjects
- Define assessment types (quiz, exam, project) with weights
- Create assessment templates that can be reused
- Record and grade pupil assessments
- Automatic calculation of percentages and letter grades

### Communication
- Messaging system between users
- School-wide and targeted announcements
- Notification system for important updates
- Track read status of messages and notifications

## Technology Stack

- **Backend**: Django (Python)
- **Database**: SQLite (default) or PostgreSQL
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Additional Libraries**: 
  - qrcode: For generating QR codes
  - Pillow: For image processing
  - django-crispy-forms: For form rendering
  - django-tables2: For data tables
  - django-filter: For filtering data
  - django-import-export: For importing/exporting data

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd school-management-system
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Access the admin interface at http://127.0.0.1:8000/admin/

## Project Structure

The project is organized into several Django apps:

- **users**: Custom user model with role-based permissions
- **pupils**: Pupil records and QR code generation
- **attendance**: QR code-based attendance tracking
- **assessments**: Subject, assessment, and grading management
- **communication**: Messaging, announcements, and notifications

## Usage

### Admin Interface

The Django admin interface provides access to all models and functionality:

1. Log in with your superuser credentials
2. Manage users, pupils, grades, attendance, assessments, and communication
3. Use the inline forms to manage related records efficiently

### QR Code Attendance System

1. Each pupil has a unique QR code generated automatically
2. Create an attendance session for a specific grade and period
3. Scan pupil QR codes to mark attendance
4. View attendance reports and statistics

### Assessment Management

1. Create subjects and assessment types
2. Define grading scales
3. Create assessment templates
4. Assign assessments to grades
5. Record and grade pupil results

### Communication

1. Create message threads with multiple participants
2. Send and receive messages
3. Create and publish announcements
4. Manage notifications

## Future Enhancements

- Mobile app for QR code scanning
- Parent portal for viewing pupil information
- Advanced reporting and analytics
- Integration with other school systems
- Calendar and scheduling features

## License

This project is licensed under the MIT License - see the LICENSE file for details.#   S c h o o l - M a n a g m e n t - S y s t e m  
 