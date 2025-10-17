// Get references to our HTML elements
const analyzeButton = document.getElementById('analyze-button');
const scoreCircle = document.getElementById('score-circle');
const scoreText = document.getElementById('score-text');
const reasonText = document.getElementById('reason-text');

// Add a click listener to our button
analyzeButton.addEventListener('click', async () => {
    // Step 1: Get the current active tab in Chrome
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Step 2: Run our content.js script on that tab
    const [injectionResult] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js'],
    });

    const pageContent = injectionResult.result;
    const textToAnalyze = `${pageContent.title}. ${pageContent.paragraph}`;
    console.log("Sending to backend:", textToAnalyze); 

    reasonText.innerText = "Analyzing...";

    // Step 3: Send the extracted text to our backend API
    try {
        const response = await fetch('http://127.0.0.1:8000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textToAnalyze }),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const analysis = await response.json();

        // Step 4: Update the UI with the result
        updateUI(analysis);

    } catch (error) {
        reasonText.innerText = "Failed to analyze. Is the server running?";
        console.error(error);
    }
});

function updateUI(analysis) {
    scoreText.innerText = `${analysis.score}%`;
    reasonText.innerText = analysis.reasons[0] || 'Looks good!';

    // Change the circle's border color based on the score
    if (analysis.score > 70) {
        scoreCircle.style.borderColor = 'green';
    } else if (analysis.score > 40) {
        scoreCircle.style.borderColor = 'orange';
    } else {
        scoreCircle.style.borderColor = 'red';
    }
}