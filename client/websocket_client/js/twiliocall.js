let twilioCallActive = true;
let twilioInterval;

// Function to trigger the warning alert dynamically
function triggerWarning(message) {
    document.getElementById('alertMessage').innerHTML = `⚠️ ${message}`;
    document.getElementById('alertBox').style.display = "block";
    startTwilioCall();
}


// Simulating repeated calls every 20s
twilioInterval = setInterval(() => {
    checkCondition()

    console.log("🚨 Twilio is making another call...");
}, 60000);

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
      
      fetch(`http://${hostname}:9000/change_twilio_call_answered_status`, requestOptions)
        .then((response) => response.text())
        .then((result) => console.log(result))
        .catch((error) => console.error(error));


        twilioCallActive = false;
        // clearInterval(twilioInterval);
        document.getElementById('alertBox').style.display = "none";

}