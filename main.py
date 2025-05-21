import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime, date
import time

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://smart-attendance-system-f285d-default-rtdb.firebaseio.com/",
    "storageBucket": "smart-attendance-system-f285d.appspot.com"
})

bucket = storage.bucket("smart-attendance-system-f285d.appspot.com")

# Setup camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load background image
imgBackground = cv2.imread('Resources/background.png')

# Load mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]

# Load the encoding file
print("Loading Encode File ...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

# Initialize variables
modeType = 0
counter = 0
id = -1
imgStudent = []

def blend_images(bg_img, overlay_img, alpha=0.5, x=0, y=0):
    """Blend overlay_img on bg_img at position (x, y) with alpha transparency."""
    h, w = overlay_img.shape[:2]
    roi = bg_img[y:y+h, x:x+w]
    blended = cv2.addWeighted(roi, 1 - alpha, overlay_img, alpha, 0)
    bg_img[y:y+h, x:x+w] = blended

def smooth_transition(img1, img2, steps=10):
    """Create a smooth transition effect between two images."""
    for alpha in np.linspace(0, 1, steps):
        blended = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
        cv2.imshow("Face Attendance", blended)
        cv2.waitKey(100)

while True:
    success, img = cap.read()
    if not success:
        break

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    blend_images(imgBackground, imgModeList[modeType], alpha=0.8, x=808, y=44)

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]
                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

        if counter != 0:
            if counter == 1:
                # Get the Data
                studentInfo = db.reference(f'Employees/{id}').get()
                print(studentInfo)
                # Get the Image from the storage
                blob = bucket.get_blob(f'Images/{id}.png')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
                # Compare the last attendance date with today's date
                last_attendance_time = studentInfo['last_attendance_time']
                last_attendance_date = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S").date()
                today_date = date.today()

                if last_attendance_date == today_date:
                    modeType = 2  # Already marked for today
                    print("Attendance already marked today. Displaying mode 2.")
                else:
                    ref = db.reference(f'Employees/{id}')
                    studentInfo['total_attendance'] += 1
                    ref.child('total_attendance').set(studentInfo['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    modeType = 1  # Successfully updated attendance
                    print("Attendance updated. Displaying mode 1.")

            if modeType != 2:
                if 10 < counter < 20:
                    # Adding a smooth transition to mode 2
                    smooth_transition(imgBackground, imgModeList[2], steps=30)
                    modeType = 2
                    # Adding a delay of 2 seconds before switching to mode 2
                    time.sleep(2)

                blend_images(imgBackground, imgModeList[modeType], alpha=0.8, x=808, y=44)

                if counter <= 10:
                    cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['department_code']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                counter += 1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    studentInfo = []
                    imgStudent = []
                    blend_images(imgBackground, imgModeList[modeType], alpha=0.8, x=808, y=44)
    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()


# from flask import Flask, render_template, Response
# from flask_socketio import SocketIO, emit
# import os
# import pickle
# import numpy as np
# import cv2
# import face_recognition
# import cvzone
# import firebase_admin
# from firebase_admin import credentials, db, storage
# from datetime import datetime, date
# import threading
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app)
#
# # Initialize Firebase
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred, {
#     "databaseURL": "https://smart-attendance-system-f285d-default-rtdb.firebaseio.com/",
#     "storageBucket": "smart-attendance-system-f285d.appspot.com"
# })
#
# bucket = storage.bucket("smart-attendance-system-f285d.appspot.com")
#
# # Load encoding file
# print("Loading Encode File ...")
# with open('EncodeFile.p', 'rb') as file:
#     encodeListKnownWithIds = pickle.load(file)
# encodeListKnown, studentIds = encodeListKnownWithIds
# print("Encode File Loaded")
#
# # Global variables
# cap = cv2.VideoCapture(0)
# modeType = 0
# counter = 0
# id = -1
# imgStudent = []
#
#
# @app.route('/')
# def index():
#     return render_template('index.html')
# def detect_faces():
#     global modeType, counter, id, imgStudent
#     while True:
#         success, img = cap.read()
#         if not success:
#             break
#
#         imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
#         imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
#
#         faceCurFrame = face_recognition.face_locations(imgS)
#         encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
#
#         if faceCurFrame:
#             for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
#                 matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
#                 faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
#                 matchIndex = np.argmin(faceDis)
#
#                 if matches[matchIndex]:
#                     id = studentIds[matchIndex]
#                     if counter == 0:
#                         counter = 1
#                         modeType = 1
#
#             if counter != 0:
#                 if counter == 1:
#                     studentInfo = db.reference(f'Employees/{id}').get()
#                     blob = bucket.get_blob(f'Images/{id}.png')
#                     array = np.frombuffer(blob.download_as_string(), np.uint8)
#                     imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
#                     last_attendance_time = studentInfo['last_attendance_time']
#                     last_attendance_date = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S").date()
#                     today_date = date.today()
#
#                     if last_attendance_date == today_date:
#                         modeType = 2  # Already marked for today
#                     else:
#                         ref = db.reference(f'Employees/{id}')
#                         studentInfo['total_attendance'] += 1
#                         ref.child('total_attendance').set(studentInfo['total_attendance'])
#                         ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#                         modeType = 1  # Successfully updated attendance
#
#                 if modeType != 2:
#                     if 10 < counter < 20:
#                         modeType = 2
#                         counter = 0
#                         emit('face_detected', {
#                             'total_attendance': studentInfo.get('total_attendance', 0),
#                             'department_code': studentInfo.get('department_code', ''),
#                             'name': studentInfo.get('name', ''),
#                             'image': imgStudent.tolist()
#                         }, broadcast=True)
#                 counter += 1
#         else:
#             modeType = 0
#             counter = 0
#
#
# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')
#
#
# @socketio.on('disconnect')
# def handle_disconnect():
#     print('Client disconnected')
#
#
# def gen_frames():
#     while True:
#         success, frame = cap.read()
#         if not success:
#             break
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#
# @app.route('/video_feed')
# def video_feed():
#     return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
#
#
# if __name__ == '__main__':
#     t = threading.Thread(target=detect_faces)
#     t.daemon = True
#     t.start()
#     socketio.run(app, debug=True)
# app.py