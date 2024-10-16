import sqlite3

# create the database
conn = sqlite3.connect('habit_tracker.db')
cursor = conn.cursor()

# 1. User Database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL, -- This should be hashed
        role TEXT CHECK(role IN ('Child', 'Parent', 'Teacher')),
        accessibility_settings TEXT,
        profile_customizations TEXT,
        registration_date TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

# 2. Habit Database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Habits (
        habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER  NULL,
        habit_name TEXT NOT NULL,
        description TEXT,
        frequency TEXT CHECK(frequency IN ('Daily', 'Weekly')),
        start_date TEXT,
        end_date TEXT,
        status TEXT CHECK(status IN ('Active', 'Inactive')),
        FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
''')

# 3. Task Database - user_id added
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        user_id INTEGER NULL,  -- User ID to track task ownership
        task_name TEXT NOT NULL,
        due_date TEXT,
        status TEXT CHECK(status IN ('Completed', 'Pending')),
        completion_date TEXT,
        reward_earned TEXT,
        FOREIGN KEY(habit_id) REFERENCES Habits(habit_id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE  -- Foreign key for user_id
    )
''')

# 4. Content Database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_type TEXT CHECK(content_type IN ('Video', 'PDF', 'Assignment')),
        upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
        uploaded_by INTEGER NOT NULL, -- Teacher ID (from Users table)
        associated_habits TEXT, -- Could be multiple habits (serialized as a list or string)
        FOREIGN KEY(uploaded_by) REFERENCES Users(user_id) ON DELETE SET NULL
    )
''')

# 5. Analytics Database
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Analytics (
        analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_completion_rate REAL,
        habit_progress REAL, -- Percentage of completion
        feedback TEXT,
        date_of_analysis TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
''')


# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")
