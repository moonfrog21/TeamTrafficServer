# TeamTrafficServer 🚦

## Overview & Purpose
TeamTrafficServer is a prototype which acts as a dedicated backend platform engineered to receive telemetry from TeamTrafficApp users, visualize this information, and transmit real-time updates to IoT-enabled traffic light controllers. This centralized web server was explicitly developed for the IEEE IAS Design Competition.

## Current Prototype
The system is currently hosted locally and ingests incoming telemetry securely through an ngrok encrypted tunnel. It renders the live GPS coordinates and active user metrics within structured tables on the frontend dashboard.

## Features to Add to Prototype
-Plot active users dynamically on an interactive geographical map.
-Implement control logic enabling queued vehicles at intersections to autonomously trigger traffic light state changes.
-Establish communication with ESP32 IoT hardware.

# Download and setup

## 1. System Setup (Windows)

0. **Git clone the repo:** save to a windows file path using git clone.
1. **Install Python:** Download Python 3.x from python.org. make sure it is setup correctly
2. **Open Terminal & Set Execution Policy:** Open PowerShell and run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
3. **Create and Activate Virtual Environment:** In your project folder, run `python -m venv .venv`. Activate it using `.venv\Scripts\activate`.
4. **Install Dependencies:** With the environment active, run `pip install -r requirements.txt`.

## 2. Starting the Server and Webpage(for viewing webpage on browser)

1. **Verify Environment and Directory:** Ensure your virtual environment is active(`.venv\Scripts\activate`), then enter the main directory(TeamTrafficServer).
2. **Run the Server:** Start the application by running `python run.py`. Keep this terminal open.
3. **Access in Browser:** Navigate to `http://127.0.0.1:9998/` in your web browser.

## 3. Starting Ngrok Tunneling Service(so that app can send live data)

1. **Install and Configure Ngrok:** Download from ngrok.com/download/windows, extract the executable, and add your auth token.
2. **Start the HTTP Tunnel:** Open a **new** terminal window and run `ngrok http 9998`.
3. **Update App Configuration:** Copy the generated Forwarding URL from the terminal and paste it into your app's configuration.
