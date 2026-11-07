# ProjectHub – Engineering Project Management Dashboard

ProjectHub is a web-based Engineering Project Management and Risk Tracking Dashboard developed using Python Flask. It helps users organize engineering projects, manage tasks, monitor progress, and identify potential project risks through a centralized dashboard.

## 🚀 Features

- **User Authentication:** Secure user registration, login and logout.
- **Dashboard:** View project statistics and task summaries.
- **Project Management:** Create, view, update and delete projects.
- **Task Management:** Add, edit, delete and track project tasks.
- **Risk Management:** Identify, assess and manage project risks based on probability and impact.
- **Risk Assessment:** Automatically calculate risk levels (Low, Medium and High).
- **Analytics:** Visualize task status and project progress using charts.
- **Search and Filtering:** Easily find and filter projects, tasks and risks.
- **Responsive Design:** User-friendly interface for desktop, tablet and mobile devices.
- **Data Security:** Password hashing, CSRF protection and user-specific data access.

## 🛠️ Technologies Used

| Category | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask Sessions |
| Security | Flask-WTF, CSRF Protection, Werkzeug |
| Charts | Chart.js |
| Environment Management | python-dotenv |
| Version Control | Git and GitHub |

## 📂 Project Structure

```text
ProjectHub/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── tasks.html
│   └── risks.html
│
└── instance/
    └── projects.db
```

*Note: The `instance/` directory and `.env` file are excluded from the GitHub repository.*

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Anubindh/ProjectHub.git
```

### 2. Navigate to the Project Directory

```bash
cd ProjectHub
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the main project directory and add:

```env
SECRET_KEY=your_random_secret_key
```

Generate a secure secret key using:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into your `.env` file.

### 7. Run the Application

```bash
python app.py
```

### 8. Open in Browser

```text
http://127.0.0.1:5000
```

Register an account and start managing your engineering projects!

## 🔐 Security

ProjectHub incorporates several security measures:

- Password hashing.
- CSRF protection for forms.
- Login-protected application routes.
- User-specific project, task and risk management.
- Environment-based secret key configuration.
- Session and cache security controls.

## 🎯 Project Objective

The primary objective of ProjectHub is to simplify engineering project management by providing a centralized platform for organizing projects, tracking tasks, monitoring progress and managing potential risks.

## 👨‍💻 Developer

**ANUBINDH P**

GitHub: [Anubindh](https://github.com/Anubindh)

---

⭐ If you find this project useful, consider giving the repository a star!
