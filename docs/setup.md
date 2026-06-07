# Setup & Installation Guide

Follow these steps to get the development environment running on your local machine.

## 1. Prerequisites
Before installing the dependencies, ensure you have the following:
* **Python 3.8+**: This project requires a modern Python environment. Check your version with `python --version`.
* **pip**: The Python package installer (usually included with Python).
* **Virtual Environment (Recommended)**: To avoid conflicts with other projects.

## 2. Installation

### Clone the Repository
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### Create a Virtual Environment
It is highly recommended to use a virtual environment to keep dependencies isolated.
```bash
# Create the environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies
Install the required libraries listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

## 3. Configuration (.env)
The application requires environment variables to manage secrets and settings.

1. Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and fill in your specific values (API keys, Database URLs, etc.). 
> **Note:** Never commit your `.env` file to version control.

## 4. Running the Application
Once the setup is complete, you can start the project using:
```bash
python main.py
```

## Troubleshooting
* **Missing Dependencies:** If a library fails to install, ensure your `pip` is up to date: `pip install --upgrade pip`.
* **Environment Errors:** Double-check that your `.env` file is in the root folder and the keys match the names used in the code.
