from email.message import Message
from flask import Flask, render_template, redirect, url_for, flash, request, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import smtplib

app = Flask(__name__)
app.secret_key = '4e4f7a3f49c658f7e2f2e3be3c6e3d2e682c1c3e4e2fcd11f40c3b487c3a19c5'  # Replace with your generated key



# Token serializer
s = URLSafeTimedSerializer(app.secret_key)

# SQLite connection function
def get_db_connection():
    conn = sqlite3.connect('habit_tracker.db')
    conn.row_factory = sqlite3.Row  # To fetch rows as dictionaries
    return conn

@app.route('/', methods=['GET'])
def index():
    if 'email' in session:
        user_id = session['user_id']
        
        # Fetch counts and course names
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get count of enrolled courses
        cursor.execute('SELECT COUNT(*) as enrolled_count FROM Habits WHERE user_id = ?', (user_id,))
        enrolled_count = cursor.fetchone()['enrolled_count']
        
        # Get count of completed courses
        cursor.execute('SELECT COUNT(*) as completed_count FROM Habits WHERE user_id = ? AND status = ?', 
                       (user_id, 'Completed'))
        completed_count = cursor.fetchone()['completed_count']
        if completed_count is None:
            completed_count = 0
        # Fetch enrolled courses and their progress
        cursor.execute('SELECT habit_name, status FROM Habits WHERE user_id = ?', (user_id,))
        enrolled_courses = cursor.fetchall()
        
        conn.close()
        
        return render_template('home.html', user=session, 
                               enrolled_count=enrolled_count, 
                               completed_count=completed_count,
                               enrolled_courses=enrolled_courses)
    else:
        return render_template('index.html', user=None)

    


# Signup route for users to sign up manually
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # Child, Parent, Teacher
        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)  # Default hashing method
        print(name,email,password,role,registration_date,hashed_password)
        try:
            # Insert user into database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Users (name, email, password, role, registration_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, hashed_password, role, registration_date))
            conn.commit()
            conn.close()
            print('signuped')
            flash('Signup successful! Please log in.')
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Users WHERE email = ?', (email,))
            user = cursor.fetchone()
        # print(user)
            conn.close()
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['name'] = user['name']
            return redirect(url_for('index'))

        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different one.')
            return redirect(url_for('signup'))

    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
       # print(email,password)
        # Fetch the user by email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = ?', (email,))
        user = cursor.fetchone()
       # print(user)
        conn.close()
       # print(check_password_hash(user['password'], password))

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['name'] = user['name']
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and password.')
            print('login failed')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/profile_update', methods=['GET', 'POST'])
def profile_update():
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch the user from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        print(name, email, password)

        # Update user details
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE Users SET name = ?, email = ? WHERE user_id = ?', (name, email, user_id))
        if password:  
            hashed_password = generate_password_hash(password)
            cursor.execute('UPDATE Users SET password = ? WHERE user_id = ?', (hashed_password, user_id))

        conn.commit()
        conn.close()
        flash('Profile updated successfully!')
        return redirect(url_for('index'))

    return render_template('profile_update.html', user=user)


# Password recovery route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Generate a token
            token = s.dumps(email, salt='password-reset-salt')
            reset_link = url_for('reset_password', token=token, _external=True)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login( 'shyamraghav12@gmail.com','ccqm klcv qnpz dgmy')
            server.sendmail( 'shyamraghav12@gmail.com', email, f'Your password reset link is: {reset_link}')
            # # Send the email
            msg = Message('Password Reset Request',
                              sender='shyamraghav12@gmail.com',
                              recipients=[email])
            msg.body = f'Your password reset link is: {reset_link}'
            email.send(msg)  # Send the email
            print('Mail sent')

            flash('A password reset link has been sent to your email address.')
            return redirect(url_for('login'))
        else:
            flash('No account associated with this email.')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

# Password reset route
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # Token valid for 1 hour
    except Exception:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Users SET password = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        conn.close()

        flash('Your password has been updated successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


@app.route('/setgoals')
def setgoals():
    return render_template('set_goals.html')


@app.route('/progress')
def progress():
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch enrolled habits (courses) for the user
    cursor.execute('''
        SELECT h.habit_id, h.habit_name 
        FROM Habits h 
        WHERE h.user_id = ?
    ''', (user_id,))
    enrolled_habits = cursor.fetchall()
    
    progress_data = []

    for habit in enrolled_habits:
        habit_id = habit['habit_id']
        
        # Calculate total tasks and completed tasks for each habit
        cursor.execute('SELECT COUNT(*) as total_tasks FROM Tasks WHERE habit_id = ? AND user_id = ?', (habit_id, user_id))
        total_tasks = cursor.fetchone()['total_tasks']
        
        cursor.execute('SELECT COUNT(*) as completed_tasks FROM Tasks WHERE habit_id = ? AND user_id = ? AND status = ?', 
                       (habit_id, user_id, 'Completed'))
        completed_tasks = cursor.fetchone()['completed_tasks']
        
        # Calculate completion percentage
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        progress_data.append({
            'habit_name': habit['habit_name'],
            'completion_percentage': completion_percentage
        })

    conn.close()
    return render_template('progress.html', progress_data=progress_data, user=session)



@app.route('/sync')
def sync():
    return render_template('sync.html')

@app.route('/notification')
def notification():
    return render_template('notification.html')

@app.route('/parental_monitoring')
def parental_monitoring():
    return render_template('parental_monitoring.html')

@app.route('/user_analysis')
def user_analysis():
    return render_template('user_analysis.html')


@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        habit_name = request.form['habit_name']
        description = request.form['description']
        frequency = request.form['frequency']

        # Insert new course into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Habits (habit_name, description, frequency, status)
            VALUES (?, ?, ?, 'Active')
        ''', (habit_name, description, frequency))
        conn.commit()
        conn.close()

        return redirect(url_for('courses'))  # Redirect to the course listing page after adding

    return render_template('add_course.html')  # Render the add course page




@app.route('/enroll/<course_name>', methods=['GET', 'POST'])
def enroll(course_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user is already enrolled in the course (habit)
    cursor.execute('SELECT * FROM Habits WHERE user_id = ? AND habit_name = ?', 
                   (session['user_id'], course_name))
    habit = cursor.fetchone()

    if not habit:
        # If the user is not enrolled, create a new habit
        cursor.execute('INSERT INTO Habits (user_id, habit_name, description, frequency, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                       (session['user_id'], course_name, f"Study {course_name}", 'Weekly', datetime.now().strftime("%Y-%m-%d"), None, 'Active'))
        habit_id = cursor.lastrowid

        # Create initial tasks for the course
        cursor.execute('INSERT INTO Tasks (habit_id, user_id, task_name, due_date, status) VALUES (?, ?, ?, ?, ?)', 
                       (habit_id, session['user_id'], 'Complete first assignment', datetime.now().strftime("%Y-%m-%d"), 'Pending'))

        conn.commit()
        
        flash(f'Successfully enrolled in {course_name}!', 'success')
        return render_template('course_enroll.html', course_name=course_name, habit_id=habit_id)
    else:
        # If already enrolled, check if all tasks are completed
        cursor.execute('SELECT COUNT(*) as completed_count FROM Tasks WHERE habit_id = ? AND status = ?', 
                       (habit['habit_id'], 'Completed'))
        completed_count = cursor.fetchone()['completed_count'] or 0  # Use 0 if None

        cursor.execute('SELECT COUNT(*) as total_tasks FROM Tasks WHERE habit_id = ?', 
                       (habit['habit_id'],))
        total_tasks = cursor.fetchone()['total_tasks'] or 0  # Use 0 if None

        if total_tasks > 0:  # Ensure there are tasks to check
            if completed_count == total_tasks:
                flash(f'You have completed the course {course_name}!', 'info')
            else:
                flash(f'You are already enrolled in {course_name} but have not completed all tasks!', 'info')
        else:
            flash(f'You are already enrolled in {course_name}!', 'info')

    conn.close()
    return redirect(url_for('courses'))


@app.route('/courses')
def courses():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all courses (habits)
    cursor.execute('SELECT * FROM Habits')
    habits = cursor.fetchall()

    # Prepare a list to hold course information with enrollment status
    courses = []
    
    # Fetch all user enrolled habits
    cursor.execute('SELECT habit_id FROM Tasks WHERE user_id = ?', (session['user_id'],))
    enrolled_habits = cursor.fetchall()
    enrolled_habit_ids = {habit['habit_id'] for habit in enrolled_habits}

    for habit in habits:
        # Initialize the habit information
        habit_info = {
            'habit_id': habit['habit_id'],
            'habit_name': habit['habit_name'],
            'description': habit['description'],
            'is_enrolled': habit['habit_id'] in enrolled_habit_ids,
            'is_completed': False
        }

        # Check if the user has completed all tasks for the enrolled habit
        if habit_info['is_enrolled']:
            cursor.execute('SELECT COUNT(*) as completed_count FROM Tasks WHERE habit_id = ? AND user_id = ? AND status = ?', 
                           (habit['habit_id'], session['user_id'], 'Completed'))
            completed_count = cursor.fetchone()['completed_count'] or 0  # Handle None

            cursor.execute('SELECT COUNT(*) as total_tasks FROM Tasks WHERE habit_id = ? AND user_id = ?', 
                           (habit['habit_id'], session['user_id']))
            total_tasks = cursor.fetchone()['total_tasks'] or 0  # Handle None

            if completed_count == total_tasks and total_tasks > 0:
                habit_info['is_completed'] = True

        # Check if a habit with the same name already exists in the courses list
        existing_habit = next((course for course in courses if course['habit_name'] == habit_info['habit_name']), None)
        if existing_habit is None:
            # If it does not exist, append this habit info to the courses list
            courses.append(habit_info)
        elif habit_info['is_enrolled']:
            # If it exists and this habit is enrolled, replace it
            existing_habit.update(habit_info)

    conn.close()
    return render_template('course.html', courses=courses, user=session)


@app.route('/content_delivery/<int:habit_id>',methods=['GET', 'POST'])
def content_delivery(habit_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the content associated with the specified habit_id
    cursor.execute('''
        SELECT c.content_id, c.content_type, c.upload_date, c.uploaded_by
        FROM Content c
        JOIN Habits h ON c.associated_habits LIKE '%' || h.habit_name || '%'
        WHERE h.habit_id = ?
    ''', (habit_id,))
    content = cursor.fetchall()

    # Fetch the habit details to display on the page
    cursor.execute('SELECT habit_name, description FROM Habits WHERE habit_id = ?', (habit_id,))
    habit = cursor.fetchone()

    conn.close()

    return render_template('content_delivery.html', content=content, habit=habit)



@app.route('/rewards')
def rewards():
    return render_template('rewards.html')


@app.route('/logout')
def logout():
    session.clear()  # Clears all session data
    flash('Logged out successfully.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
