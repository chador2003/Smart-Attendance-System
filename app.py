import os
import pickle
import numpy as np
import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, Response, jsonify, redirect, url_for, session, request
import csv
from flask import send_file

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://smart-attendance-system-f285d-default-rtdb.firebaseio.com/",
    "storageBucket": "smart-attendance-system-f285d.appspot.com"
})

bucket = storage.bucket("smart-attendance-system-f285d.appspot.com")

# Initialize Flask app
app = Flask(__name__)

# Load the encoding file
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds

# Initialize variables
counter = 0
id = -1
imgStudent = []
studentInfo = {}

# Setup camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
app.secret_key = 'elephant'  # Replace with a real secret key

# Admin credentials (in a real app, use a database and hashed passwords)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials, please try again."

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/download_csv', methods=['POST'])
@login_required
def download_csv():
    # Prepare data for CSV
    employees = db.reference('Employees').get()
    csv_data = []
    for id, details in employees.items():
        csv_data.append([id, details['name'], details['absent_days']])

    # Set up CSV file parameters
    filename = "employee_details.csv"
    csv_columns = ['ID', 'Name', 'Absent Days']

    # Create CSV file
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_columns)
        writer.writerows(csv_data)

    # Send the CSV file as a response
    return send_file(filename, as_attachment=True)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    employees = db.reference('Employees').get()
    return render_template('details.html', employees=employees)

def calculate_absent_days(last_attendance_date):
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)
    if last_attendance_date < first_day_of_month:
        last_attendance_date = first_day_of_month
    absent_days = (today - last_attendance_date).days - 1
    return max(absent_days, 0)

def generate_frames():
    global counter, id, imgStudent, studentInfo
    while True:
        success, img = cap.read()
        if not success:
            break

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    id = studentIds[matchIndex]
                    if counter == 0:
                        counter = 1

            if counter != 0:
                if counter == 1:
                    studentInfo = db.reference(f'Employees/{id}').get()
                    blob = bucket.get_blob(f'Images/{id}.png')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    last_attendance_time = studentInfo['last_attendance_time']
                    last_attendance_date = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S").date()
                    today_date = date.today()

                    # Check for absence and update database
                    if last_attendance_date != today_date:
                        absent_days = calculate_absent_days(last_attendance_date)
                        studentInfo['total_attendance'] += 1
                        studentInfo['attendance_status'] = 'Attendance marked'
                        studentInfo['absent_days'] = absent_days

                        # Add the current date to absent_dates if it's not already present
                        absent_dates = studentInfo.get('absent_dates', [])
                        if today_date.strftime("%Y-%m-%d") not in absent_dates:
                            absent_dates.append(today_date.strftime("%Y-%m-%d"))
                            ref = db.reference(f'Employees/{id}')
                            ref.child('absent_dates').set(absent_dates)

                        # Update database records
                        ref.child('total_attendance').set(studentInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        ref.child('absent_days').set(absent_days)
                    else:
                        studentInfo['attendance_status'] = 'Already marked'

                counter += 1

                if counter >= 20:
                    counter = 0
                    studentInfo = {}
                    imgStudent = []

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/attendance_info')
def attendance_info():
    return jsonify(studentInfo)

if __name__ == "__main__":
    app.run(debug=True)
