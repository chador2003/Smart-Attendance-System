  function fetchAttendanceInfo() {
            fetch('/attendance_info')
                .then(response => response.json())
                .then(data => {
                    document.querySelector('#name .value').textContent = data.name || '';
                    document.querySelector('#total_attendance .value').textContent = data.total_attendance || '';
                    document.querySelector('#absent_days .value').textContent = data.absent_days || '';
                    document.querySelector('#department .value').textContent = data.department || '';
                    document.querySelector('#status .value').textContent = data.attendance_status || '';
                });
        }
        setInterval(fetchAttendanceInfo, 1000);
