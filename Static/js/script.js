document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById('video');
    const nameElement = document.getElementById('name');
    const statusElement = document.getElementById('status');

    // Access the user's camera
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(err => {
            console.error('Error accessing the camera: ', err);
        });

    // Dummy data for detected face details

    // Function to update face details (This would be dynamic in a real application)
    function updateFaceDetails(details) {
        nameElement.textContent = `Name: ${details.name}`;
        statusElement.textContent = `Status: ${details.status}`;
    }

    // Simulate detecting a face after 3 seconds
    setTimeout(() => {
        updateFaceDetails(faceDetails);
    }, 3000);
});
