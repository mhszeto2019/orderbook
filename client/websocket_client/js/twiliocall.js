let twilioCallActive = true;
let twilioInterval;

// Function to trigger the warning alert dynamically
function triggerWarning(message) {
    document.getElementById('alertMessage').innerHTML = `⚠️ ${message}`;
    document.getElementById('alertBox').style.display = "block";
    startTwilioCall();
}

// Simulate condition for triggering warning
function checkCondition() {

    const formdata = new FormData();
    formdata.append("username", localStorage.getItem('username'));
    const check_alert_status = {
        method: "POST",
        body: formdata,
      };
    fetch("http://127.0.0.1:9000/change_twilio_call_answered_status", check_alert_status)
    .then((response) => response.text())
    .then((result) => console.log(result))
    .catch((error) => console.error(error));

    console.log(result)
    twilioCallActive = false;
    // clearInterval(twilioInterval);
    document.getElementById('alertBox').style.display = "none";
}

// Simulate Twilio Call (Replace this with actual Twilio API call)
function startInterval() {
    // Simulating repeated calls every 20s
    twilioInterval = setInterval(() => {
        checkCondition()
        console.log("🚨 Twilio is making another call...");
    }, 2000);
}

// Stop Twilio Calls
async function stopTwilioCall() {

    console.log("⛔ Twilio calls stopped.");
    const formdata = new FormData();
    formdata.append("username", localStorage.getItem('username'));
    formdata.append("status", "True");
    const requestOptions = {
        method: "POST",
        body: formdata,
      };
      
      fetch("http://127.0.0.1:9000/change_twilio_call_answered_status", requestOptions)
        .then((response) => response.text())
        .then((result) => console.log(result))
        .catch((error) => console.error(error));


        twilioCallActive = false;
        // clearInterval(twilioInterval);
        document.getElementById('alertBox').style.display = "none";

}