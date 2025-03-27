let twilioCallActive = false;
let twilioInterval;

// Function to trigger the warning alert dynamically
function triggerWarning(message) {
    document.getElementById('alertMessage').innerHTML = `⚠️ ${message}`;
    document.getElementById('alertBox').style.display = "block";
    startTwilioCall();
}

// Simulate condition for triggering warning
function checkCondition() {
    let conditionMet = Math.random() < 0.3; // 30% chance to trigger warning (for testing)
    if (conditionMet) {
        triggerWarning("Critical Alert! Immediate action required.");
    }
}

// Simulate Twilio Call (Replace this with actual Twilio API call)
function startTwilioCall() {
    if (twilioCallActive) return;
    twilioCallActive = true;
    console.log("📞 Twilio call started...");

    // Simulating repeated calls every 20s
    twilioInterval = setInterval(() => {
        console.log("🚨 Twilio is making another call...");
    }, 20000);
}

// Stop Twilio Calls
async function stopTwilioCall() {
    // twilioCallActive = false;
    // clearInterval(twilioInterval);
    // document.getElementById('alertBox').style.display = "none";
    console.log("⛔ Twilio calls stopped.");


}