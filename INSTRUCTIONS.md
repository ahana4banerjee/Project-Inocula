Project Inocula - Local Setup & Running Instructions

This guide provides detailed, step-by-step instructions to get the complete Project Inocula stack running on your local machine. The project consists of three main components that need to be run simultaneously: the Python backend, the user dashboard, and the admin dashboard.

1. Prerequisites

Before you begin, ensure you have the following software installed on your computer:

Git: For cloning the repository.

Python (3.9+): For running the backend server.

Node.js (v16+): For running the React frontends.

Google Chrome: For testing the browser extension.

2. Initial Project Setup

First, let's get the project code onto your machine and configure the necessary secrets.

A. Clone the Repository
Open a terminal and run the following command to download the project folder:

git clone [https://github.com/your-username/Project-Inocula.git](https://github.com/your-username/Project-Inocula.git)
cd Project-Inocula


B. Set Up Secret API Keys
The backend requires API keys to function. You will need to create a .env file to store them securely.

Navigate into the backend directory:

cd backend


Create a new file named .env.

Open the .env file and paste the following content, replacing the placeholders with your actual secret keys:

# Get this from MongoDB Atlas
MONGO_CONNECTION_STRING="your_mongodb_connection_string"

# Get this from Google AI Studio
GEMINI_API_KEY="your_google_gemini_api_key"

# Get this from Hugging Face (Settings -> Access Tokens)
HF_TOKEN="your_hugging_face_read_token"


3. Backend Setup & AI Model Download

The backend requires a Python virtual environment and local copies of the AI models for offline use.

A. Create Virtual Environment & Install Dependencies
From within the backend folder:

# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate  # On Git Bash/Mac
# .\venv\Scripts\activate      # On Windows PowerShell

# Install all required Python libraries
pip install -r requirements.txt


B. Download Local AI Models
Our backend is configured to use local copies of the AI models for stability.

Make sure you have Git LFS installed (git lfs install).

From a terminal (it can be outside the project folder), clone the two model repositories:

git clone [https://huggingface.co/unitary/toxic-bert](https://huggingface.co/unitary/toxic-bert)
git clone [https://huggingface.co/j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base)


Move the two newly created folders (toxic-bert and emotion-english-distilroberta-base) into the backend directory.

4. Frontend Setup

Both the user and admin dashboards are React applications and need their dependencies installed.

A. Install User Dashboard Dependencies
Open a new terminal and navigate to the dashboard directory:

cd dashboard
npm install


B. Install Admin Dashboard Dependencies
Open a third terminal and navigate to the admin directory:

cd admin
npm install


5. Running the Full Application

You will need to have three terminals open simultaneously to run the entire project.

Terminal 1: Start the Backend Server

Navigate to the backend directory.

Ensure your virtual environment is active ((venv) should be visible).

Run the Uvicorn server:

uvicorn main:app --reload


✅ Your backend is now running at http://127.0.0.1:8000.

Terminal 2: Start the User Dashboard

Navigate to the dashboard directory.

Run the React development server:

npm start


✅ Your user dashboard is now running at http://localhost:3000.

Terminal 3: Start the Admin Dashboard

Navigate to the admin directory.

Run the React development server:

npm start


✅ Your admin dashboard is now running at http://localhost:3001.

Step 4: Load the Chrome Extension

Open Google Chrome and navigate to chrome://extensions.

Enable "Developer mode" in the top-right corner.

Click "Load unpacked" and select the extension folder from your project directory.

The Project Inocula Shield icon will appear in your browser's toolbar.

6. How to Use the System

You are now fully set up! To test the end-to-end flow:

Go to any news article website.

Click the Project Inocula Shield icon in your toolbar and click "Analyze Page".

Open the User Dashboard (localhost:3000) to see the analysis appear in your history.

From the User Dashboard, submit a report on an analysis.

Open the Admin Dashboard (localhost:3001) to see the new report and view the analytics.
