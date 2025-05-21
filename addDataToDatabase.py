import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL": "https://smart-attendance-system-f285d-default-rtdb.firebaseio.com/"
})

ref = db.reference('Employees')
data = {
    "12210034": {
        "name": "Tapash Rai",
        "department": "Emerging Technology",
        "department_code":"ET",
        "email": "tapashrai@gmail.com",
        "total_attendance": 0,
        "last_attendance_time": "2024-07-04 14:30:00",
        "absent_days":0,

    },
    "12210072": {
        "name": "Pema Wangdi",
        "department": "Emerging Technology",
        "department_code":"ET",
        "total_attendance": 0,
        "email": "pemawangdi@gmail.com",
        "last_attendance_time": "2024-07-04 14:30:00",
        "absent_days": 0,

    },
    "12210017": {
        "name": "Kinzang Wangdi",
        "department": "AI and Data Science",
        "department_code": "AI&DS",
        "total_attendance": 0,
        "email": "kinzangwangdi@gmail.com",
        "last_attendance_time": "2024-07-04 14:30:00",
        "absent_days": 0,
    },
    "12210046": {
        "name": "Dawa",
        "department": "AI and Data Science",
        "department_code": "AI&DS",
        "total_attendance": 0,
        "email": "dawa@gmail.com",
        "last_attendance_time": "2024-07-04 14:30:00",
        "absent_days": 0,
    }
}

for key, value in data.items():
    ref.child(key).set(value)
