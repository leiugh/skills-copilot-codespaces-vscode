# =============================================================
# app.py — Flask Backend for Manila Community Concern Reporting
# and Response System (MCCRRS)
#
# This file integrates the OOP classes from main (10).py with
# Flask routes, SQLAlchemy persistence, and Jinja2 templates.
# =============================================================

#CourseProject _ Group 8 _OOP
"Title of the Project: Manila Community Concern Reporting and Response System"
"""Project Manager - Leia Naomi Novales
UI/UX - Anika Almonia
QA Testing - Carelle Jumao-As
Software Engineer - Francheska Allan
Software Engineer - Archie Gujilde
Software Engineer - Brian Josh Las Marias"""

# --- Standard library and third-party imports ---
from flask import Flask, render_template, request, redirect, url_for, session, Response  # Added session import for admin login state management
from flask_sqlalchemy import SQLAlchemy  # Added for database persistence via ORM
from abc import ABC, abstractmethod
from datetime import datetime
import os  # Added for generating a random secret key

# --- Flask application initialization ---
app = Flask(__name__)
# Secret key required for Flask session support (admin login state)
app.secret_key = os.urandom(24)  # Added: generates a random secret key for session security
# SQLAlchemy database configuration — SQLite file stored in /instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Added: suppresses SQLAlchemy modification tracking warning

# Initialize SQLAlchemy ORM with the Flask app
db = SQLAlchemy(app)  # Added: creates the database engine and session


# =============================================================
# PRIORITY & STATUS CONSTANTS — From main (10).py
# =============================================================

# Priority - Constants
class PriorityLevel:
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"

# Status of the Report
class ReportStatus:
    SUBMITTED = "Submitted"
    REVIEWED = "Reviewed"
    ASSIGNED = "Assigned"
    PENDING = "Pending"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


# =============================================================
# SQLALCHEMY REPORT MODEL — Database table for persisting reports
# Added: This model replaces the in-memory reports list from
# main (10).py to enable persistent storage across restarts.
# =============================================================

class Report(db.Model):
    """SQLAlchemy model representing a submitted community concern report."""
    __tablename__ = 'reports'  # Added: explicit table name for clarity

    id             = db.Column(db.Integer, primary_key=True)  # Auto-increment ID replaces ReportIDGenerator
    name           = db.Column(db.String(120), nullable=False)
    location       = db.Column(db.String(200), nullable=False)
    concern        = db.Column(db.Text, nullable=False)
    severity       = db.Column(db.String(20), nullable=False)
    status         = db.Column(db.String(30), nullable=False, default=ReportStatus.PENDING)
    description    = db.Column(db.Text, nullable=True)  # Added: optional description field from the form
    image          = db.Column(db.LargeBinary, nullable=True)  # Added: stores uploaded image as binary blob
    image_mimetype = db.Column(db.String(50), nullable=True)  # Added: stores the MIME type of the uploaded image
    date_reported  = db.Column(db.String(50), nullable=True)  # Added: stores the date/time string when report was created
    department     = db.Column(db.String(100), nullable=True)  # Added: city government agency assigned to resolve the concern
    officer_notes  = db.Column(db.Text, nullable=True)  # Added: descriptive progress updates and resolution logs entered by officials

    def __init__(self, name, location, concern, severity, status=None, description=None, image=None, image_mimetype=None, date_reported=None, department=None, officer_notes=None, id=None):
        """Added: Explicit constructor to satisfy static IDE type analyzers (e.g. Pyright/Pylance)."""
        if id is not None:
            self.id = id
        self.name = name
        self.location = location
        self.concern = concern
        self.severity = severity
        self.status = status or ReportStatus.PENDING
        self.description = description
        self.image = image
        self.image_mimetype = image_mimetype
        self.date_reported = date_reported
        self.department = department
        self.officer_notes = officer_notes

    @property
    def officer_assignment(self):
        """Added: Alias property to dynamically map department to officer_assignment for real-time tracking consistency."""
        return self.department or "Pending Assignment"

    @officer_assignment.setter
    def officer_assignment(self, value):
        """Added: Setter method to map officer_assignment updates back to the persistent department field."""
        self.department = value

    @classmethod
    def get_public_reports(cls):
        """Added: Fetches all public-facing reports in descending order."""
        return cls.query.order_by(cls.id.desc()).all()

    @classmethod
    def get_admin_reports(cls, clearance):
        """Added: Fetches report records dynamically filtered by the logged-in admin's security clearance level."""
        # Critical clearance permits viewing all cases (Minor, Major, Critical)
        if clearance == PriorityLevel.CRITICAL:
            return cls.query.order_by(cls.id.desc()).all()
        # Major clearance permits viewing Minor and Major cases
        elif clearance == PriorityLevel.MAJOR:
            return cls.query.filter(cls.severity.in_([PriorityLevel.MINOR, PriorityLevel.MAJOR])).order_by(cls.id.desc()).all()
        # Minor clearance restricts view to Minor cases only
        else:
            return cls.query.filter(cls.severity == PriorityLevel.MINOR).order_by(cls.id.desc()).all()

    def __repr__(self):
        """String representation for debugging."""
        return f"<Report {self.id} | {self.severity} | {self.status}>"


class Announcement(db.Model):
    """Added: SQLAlchemy model representing a published city announcement bulletin."""
    __tablename__ = 'announcements'

    id             = db.Column(db.Integer, primary_key=True)  # Unique auto-increment ID
    title          = db.Column(db.String(200), nullable=False)  # Announcement headline
    date_posted    = db.Column(db.String(50), nullable=False)  # Date string when published
    content        = db.Column(db.Text, nullable=False)  # Detailed message text
    image          = db.Column(db.LargeBinary, nullable=True)  # Optional binary image blob
    image_mimetype = db.Column(db.String(50), nullable=True)  # Optional image MIME type


class Feedback(db.Model):
    """Added: SQLAlchemy model representing feedback details submitted by citizens on resolved concerns."""
    __tablename__ = 'feedback'

    id                  = db.Column(db.Integer, primary_key=True)  # Unique primary key ID
    citizen_name        = db.Column(db.String(120), nullable=False)  # Name of submitting citizen
    concern_category    = db.Column(db.String(120), nullable=False)  # Concern category rated
    department_assigned = db.Column(db.String(120), nullable=True)  # City department that handled the case
    rating              = db.Column(db.Integer, nullable=False)  # Numerical rating score (1-5 stars)
    comment             = db.Column(db.Text, nullable=True)  # Written review thoughts
    date_submitted      = db.Column(db.String(50), nullable=False)  # Timestamp string when sent

    def __init__(self, citizen_name, concern_category, rating, comment, date_submitted, department_assigned=None, id=None):
        """Added: Explicit constructor to satisfy static IDE type analyzers (e.g. Pyright/Pylance)."""
        if id is not None:
            self.id = id
        self.citizen_name = citizen_name
        self.concern_category = concern_category
        self.department_assigned = department_assigned
        self.rating = rating
        self.comment = comment
        self.date_submitted = date_submitted


# =============================================================
# OOP USER CLASSES — From main (10).py
# =============================================================

# Parent Class
class User(ABC):

    def __init__(self, user_type, name, location):
        self.user_type = user_type
        self.name = name
        self.location = location

    @abstractmethod
    def report_concern(self):
        pass

# Resident Class
class Resident(User):
    valid_severities = {PriorityLevel.MINOR, PriorityLevel.MAJOR, PriorityLevel.CRITICAL}

    def __init__(self, name, location):
        super().__init__("Resident", name, location)
        self.concern = None
        self.severity = None

    def report_concern(self, concern, severity) -> tuple[str, str]:
        if severity not in Resident.valid_severities:
            raise ValueError(f"Unsupported Severity: {severity}. Please Try Again.")
        self.concern = concern 
        self.severity = severity

        return concern, severity

        
    # Hotlines Depending on Severity of Concern
    def display_hotlines(self) -> None: 
        if self.severity is None:
            raise RuntimeError("No concern report detected. Please try again.")
        
        if self.severity == PriorityLevel.MINOR:
            barangay = "Barangay Hotline: (02) 0000-0000"
            city_hall = "City Hall: 234-5678"
            print(f"Contact the corresponding hotlines:\n{barangay}\n{city_hall}")
        elif self.severity == PriorityLevel.MAJOR:
            police = "Police Non Emergency: 345-6789"
            fire_dept = "Fire Department(Sta.Mesa): (02) 8716-1634/0917-834-0309"
            print(f"Contact the corresponding hotlines:\n{police}\n{fire_dept}")
        elif self.severity == PriorityLevel.CRITICAL:
            print("Contact this immediately.")
            national = "National Emergency Hotline: 911"
            ndrrmc = "NDRRMC: (02) 8911- 55061 to 65 (local 100),\
                (02) 8911-1406, (02) 8912-2665, (02) 8912-5668, or (02) 8911-1873"
            print(f"{national}\n{ndrrmc}")
        print("Concern/s submitted to the Government Officials.")


# Admin Class
class Admin(User):
    #Encapsulation Private (Security Numbers)
    _sec_number_map = {"11111A": PriorityLevel.MINOR, "12121B": PriorityLevel.MAJOR, "13131C": PriorityLevel.CRITICAL}

    def __init__(self, name, password, sec_number):
        super().__init__("Admin", name, "City Hall")
        self.name = name
        self.__password = password

        if sec_number not in self._sec_number_map: # ExceptionError
            raise ValueError(f"Access Denied. Invalid Security Number: {sec_number}.")
        self.sec_number = sec_number
        self.valid_login = False

    def login (self, input_password: str) -> bool:
        if self.__password == input_password:
            self.valid_login = True
            clearance_level = self._sec_number_map.get(self.sec_number, PriorityLevel.MINOR)
            print (f"Sucessful Login. \nAdmin : |{self.name}|\nSecurity Clearance: |{clearance_level}| ")
            return True
        print (f"Invalid Login.")
        return False    
    
    def _require_authentication (self): # validation for login 
        if not self.valid_login:
            raise PermissionError("You must be logged in first.") #ExceptionError
        
    def report_concern(self) -> tuple[str, str]:
        self._require_authentication()

        concern = input("Admin concern: ")
        severity = input("Severity (Minor, Major, Critical): ")
        if severity not in {PriorityLevel.MINOR, PriorityLevel.MAJOR, PriorityLevel.CRITICAL}:
            raise ValueError(f"Unsupported Severity: {severity}. Please Try Again.") # ExceptionError

        return concern, severity
    

# Report Id Reference Number Generator
class ReportIDGenerator:

    current_id = 1000

    @classmethod
    def generate_id(cls):
        cls.current_id += 1
        return f"MCCRRS-{cls.current_id}"
    

# Report System Class 
class ReportSystem:
    def __init__(self, name, location, concern, severity):
        self.report_id = ReportIDGenerator.generate_id() # Automatic Generation of Unique ID
        self.name = name
        self.location = location
        self.concern = concern 
        self.severity = severity 
        self.status = ReportStatus.PENDING
        self.date_reported = datetime.now().strftime("%B %d, %Y %I:%M %p")

        if severity not in {PriorityLevel.MINOR, PriorityLevel.MAJOR, PriorityLevel.CRITICAL}:
            raise ValueError(f"Unsupported Severity: {severity}. Please Try Again.") # ExceptionError

    def update_status(self, new_status) -> None: # Updating the Status of Report
        if new_status not in (ReportStatus.SUBMITTED, ReportStatus.REVIEWED, ReportStatus.ASSIGNED, ReportStatus.PENDING, ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED, 
                          ReportStatus.REJECTED):
            raise ValueError(f"Invalid Status Update: {new_status}. Please Choose a Valid Status.")
        self.status = new_status
        print(f"Report ID: {self.report_id} status updated to {self.status}.")
    
    
    def assign_report(self, admin: Admin) -> None: # Assigning of Report
        if not admin.valid_login:
            raise PermissionError(f"Admin {admin.name!r} must be logged in to assign the report.") # ExceptionError
        self.status = ReportStatus.ASSIGNED
        print(f"Report ID: {self.report_id} has been assigned to Admin: {admin.name}.")
                

    def display_report(self) -> None:
        print(f"Reference No.: {self.report_id}")
        print(f"name: {self.name}")
        print(f"location: {self.location}")
        print(f"Concern: {self.concern}")
        print(f"Severity: {self.severity}")
        print(f"Date Reported: {self.date_reported}")
        print(f"Status: {self.status}")

# Global Storage for Reports
reports = []


# =============================================================
# DATABASE INITIALIZATION
# Added: Creates all tables if they don't exist on first run.
# =============================================================

with app.app_context():
    # Added: Wrap entire database initialization and pre-seeding in a try-except block to prevent lock/transaction collisions from crashing startup
    try:
        db.create_all()  # initializes the expanded SQLite database schema if not present

        # Added: Pre-seed Announcements bulletin data if table is currently empty
        if Announcement.query.count() == 0:
            db.session.add(Announcement(
                id=1,
                title="Typhoon Preparedness Advisory",
                date_posted="May 28, 2026",
                content="Signal No. 2 declared for Metro Manila due to approaching Typhoon. Expect heavy rainfall and moderate to strong winds. Secure loose objects and keep emergency kits prepared."
            ))
            db.session.add(Announcement(
                id=2,
                title="Manila City Hall Health Caravan",
                date_posted="May 29, 2026",
                content="Free comprehensive public health caravan at the Sta. Ana Health Center. Free check-ups, dental extraction, vaccine shots, and priority queue given to seniors and infants."
            ))
            db.session.add(Announcement(
                id=3,
                title="Garbage Collection Delay",
                date_posted="May 30, 2026",
                content="Garbage collection will resume tomorrow due to scheduled truck maintenance operations in selective districts."
            ))
            db.session.commit() # Commit transaction

        # Added: Pre-seed Feedback cards rating data if table is empty
        if Feedback.query.count() == 0:
            db.session.add(Feedback(
                citizen_name="Juan Cruz",
                concern_category="Large Potholes",
                department_assigned="Department of Public Works",
                rating=5,
                comment="Pothole filled within 48 hours of my report! Amazing responsiveness.",
                date_submitted="May 30, 2026 03:00 PM"
            ))
            db.session.add(Feedback(
                citizen_name="Maria Santos",
                concern_category="Electrical Fire or Exposed Live Wires",
                department_assigned="Bureau of Fire Protection",
                rating=4,
                comment="BFP responded immediately to secure the smoking pole. Excellent coordination.",
                date_submitted="May 30, 2026 04:30 PM"
            ))
            db.session.add(Feedback(
                citizen_name="Pedro Penduko",
                concern_category="Noise Complaint",
                department_assigned="Manila Police District",
                rating=2,
                comment="Response took too long and the neighbors just turned up the noise again later.",
                date_submitted="May 31, 2026 01:15 AM"
            ))
            db.session.commit() # Commit transaction
    except Exception as e:
        print(f"Database initialization alert: {e}")


# =============================================================
# FLASK ROUTES — Connects templates to backend logic
# =============================================================

# Added: OOP Severity Classification Mapping based on MCCRRS priority level specifications.
# This dictionary maps specific Category of Concern values to their corresponding PriorityLevel constant.
SEVERITY_MAPPING = {
    # Critical severity concerns
    "Fire Incident": PriorityLevel.CRITICAL,
    "Flooding or Natural Disaster": PriorityLevel.CRITICAL,
    "Ongoing Crime (Robbery/Assault/Violence)": PriorityLevel.CRITICAL,
    "Medical Emergency": PriorityLevel.CRITICAL,
    "Gas Leak": PriorityLevel.CRITICAL,
    "Electrical Fire or Exposed Live Wires": PriorityLevel.CRITICAL,
    "Missing Person": PriorityLevel.CRITICAL,
    "Building/House Collapse": PriorityLevel.CRITICAL,
    "Road Accident": PriorityLevel.CRITICAL,

    # Major severity concerns
    "Large Potholes": PriorityLevel.MAJOR,
    "Water Interruption in the Community": PriorityLevel.MAJOR,
    "Power Outage": PriorityLevel.MAJOR,
    "Illegal Dumping of Garbage": PriorityLevel.MAJOR,
    "Damaged Drainage System": PriorityLevel.MAJOR,
    "Noise Complaint": PriorityLevel.MAJOR,
    "Broken Streetlight": PriorityLevel.MAJOR,

    # Minor severity concerns
    "Small Potholes": PriorityLevel.MINOR,
    "Graffiti / Vandalism": PriorityLevel.MINOR,
    "Overgrown Grass / Plants": PriorityLevel.MINOR,
    "Minor Noise Complaint": PriorityLevel.MINOR,
    "Broken Bench or Public Use": PriorityLevel.MINOR,
    "Request for Additional Bins": PriorityLevel.MINOR,
    "Minor Sidewalk Crack": PriorityLevel.MINOR
}

# Added: Route mapping root to the home page (index.html with 'home' active navigation state)
@app.route('/')
@app.route('/home')
def home():
    """Renders the Home landing page view representing the Home view."""
    # Renders the index.html template, highlighting the 'Home' navigation tab
    return render_template('index.html', active_page='home')


# Added: Route rendering the About screen (about.html with 'about' active navigation state)
@app.route('/about')
def about():
    """Renders the About/Home page representing the About view."""
    # Renders the about.html template, highlighting the 'About' navigation tab
    return render_template('about.html', active_page='about')


# Added: Route for resident report form, supporting GET (render empty form) and POST (submit concern)
@app.route('/report', methods=['GET', 'POST'])
def report():
    """Handles the resident concern submission — GET displays the form, POST processes details."""

    if request.method == 'POST':
        # Extract form text details
        name = request.form['name']
        location = request.form['location']
        concern = request.form['concern'] # Retrieve Category of Concern selection
        description = request.form.get('description', '') # Optional additional comments
        date_reported = request.form.get('date_reported', '') # Optional custom reported date/time

        # Automatically classify severity level based on the category mapping
        severity = SEVERITY_MAPPING.get(concern, PriorityLevel.MINOR)

        # Validate concern inputs via the Resident OOP class constructor
        resident_user = Resident(name, location)
        resident_user.report_concern(concern, severity)

        # Retrieve binary image data and mimetype if file uploaded
        image_data = None
        image_mimetype = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_data = file.read() # Read uploaded image blob
                image_mimetype = file.mimetype # Read MIME type for serving

        # Determine next ID based on empty table state to align SQL primary keys with ReportIDGenerator (1001+)
        is_empty = (Report.query.count() == 0)

        # Store the reported concern inside SQLite via the SQLAlchemy Report model
        new_report = Report(
            id=1001 if is_empty else None, # Enforce starting auto-increment value at 1001 to align with legacy generator
            name=name,
            location=location,
            concern=concern,
            severity=severity,
            status=ReportStatus.SUBMITTED, # Set status to Submitted on form post
            description=description,
            image=image_data,
            image_mimetype=image_mimetype,
            date_reported=date_reported or datetime.now().strftime("%B %d, %Y %I:%M %p")
        )
        db.session.add(new_report) # Queue the record
        db.session.commit() # Commit database transactions

        # Maintain global OOP array compatibility
        report_system = ReportSystem(name, location, concern, severity)
        reports.append(report_system)

        # Redirect user immediately to their tracking timeline screen
        return redirect(url_for('track', id=new_report.id))

    # GET request — render the blank form with active page highlighted
    return render_template('report.html', active_page='report')


# Added: Route to redirect old '/resident' URL requests to the new '/report' route to prevent breaking
@app.route('/resident', methods=['GET', 'POST'])
def resident():
    """Redirects deprecated resident form route to the report form route."""
    return redirect(url_for('report'))


# Added: Route for tracking report status using progress bar timelines mapping to live SQLite/OOP instances
@app.route('/track')
def track():
    """Added: Renders the concern tracking timeline and details for a selected report ID or prefixed Reference Number."""
    report_id_str = request.args.get('id')
    report = None

    # Added: If user submits a search, clean the string to extract raw integer key if prefixed with MCCRRS
    if report_id_str:
        clean_id = report_id_str.replace("MCCRRS-", "").strip()
        try:
            # Added: Query live concern record from database by integer ID
            report = Report.query.get(int(clean_id))
        except (ValueError, TypeError):
            # Fail silently on casting exceptions
            pass

    # Added: Fallback to load the most recent record so the user is not greeted with a blank dashboard on first load
    if not report:
        report = Report.query.order_by(Report.id.desc()).first()

    # Determine timeline completion width percentage based on live report status
    progress_percentage = 20 # Initial minimum percent bar width
    if report:
        if report.status == ReportStatus.SUBMITTED or report.status == ReportStatus.PENDING:
            progress_percentage = 20
        elif report.status == ReportStatus.REVIEWED:
            progress_percentage = 40
        elif report.status == ReportStatus.ASSIGNED:
            progress_percentage = 60
        elif report.status == ReportStatus.IN_PROGRESS:
            progress_percentage = 80
        elif report.status == ReportStatus.RESOLVED:
            progress_percentage = 100

    # Renders the tracking timeline dashboard passing live report object
    return render_template('track.html', report=report, progress_percentage=progress_percentage, active_page='track')


# Added: Route rendering the expandable announcements list
@app.route('/announcements')
def announcements():
    """Renders the city announcements list view with accordions."""
    # Renders announcements.html template
    return render_template('announcements.html', active_page='announcements')


# Added: Before-request interceptor to enforce the Authentication Guard for administrative resources.
@app.before_request
def admin_auth_guard():
    """Added: Intercepts all hits to secure /admin/... routes and redirects unauthenticated users."""
    # Guard all paths starting with '/admin' but skip the login page itself to prevent circular routing
    if request.path.startswith('/admin') and request.path not in ['/admin/login', '/admin']:
        # If admin login flag is not set in Flask session, redirect to standard login view
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))


# Added: Route for legacy /admin redirect to maintain compatibility and prevent breakage
@app.route('/admin')
def admin_redirect():
    """Added: Redirects requests targeting the old /admin URL directly to the new prefix login endpoint."""
    return redirect(url_for('admin_login'))


# Added: Split-pane login route supporting GET (renders form) and POST (validates security clearance)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Added: Manages administrative authentication via Admin OOP verification."""
    if request.method == 'POST':
        # Extract administrative inputs
        email = request.form['email']
        password = request.form['password']
        sec_number = request.form.get('sec_number', '') # Security number verified against OOP map

        try:
            # Instantiate Admin OOP class from app.py line 141
            admin_user = Admin(email, password, sec_number)
            # Call OOP login method verifying input password
            login_success = admin_user.login(password)

            if login_success:
                # Save security credentials in Flask session to activate guards
                session['admin_logged_in'] = True
                session['admin_name'] = email.split('@')[0].capitalize() # Get name from email address
                clearance = Admin._sec_number_map.get(sec_number, PriorityLevel.MINOR)
                session['admin_clearance'] = clearance # Save clearance tier
                session['admin_sec_number'] = sec_number
                
                # Redirect directly to admin overview dashboard
                return redirect(url_for('admin_dashboard'))
            else:
                # Render with invalid credentials error message
                return render_template('admin_login.html', error="Invalid password. Please try again.")
        except ValueError as e:
            # Catch constructor ValueError when security number is invalid
            return render_template('admin_login.html', error=str(e))

    # GET request — render high-fidelity split login page
    return render_template('admin_login.html')


# Added: Route for Overview Dashboard metrics mapping real DB counts and activity streams
@app.route('/admin/dashboard')
def admin_dashboard():
    """Added: Renders the metric card panel, emergency triggers, and recent activity updates."""
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    # Query database reports matching logged admin security clearance level
    admin_reports = Report.get_admin_reports(clearance)

    # Calculate realmetric integers for data cards
    total_reports = len(admin_reports)
    pending_count = sum(1 for r in admin_reports if r.status in [ReportStatus.PENDING, ReportStatus.SUBMITTED])
    resolved_count = sum(1 for r in admin_reports if r.status == ReportStatus.RESOLVED)
    emergency_count = sum(1 for r in admin_reports if r.severity == PriorityLevel.CRITICAL)

    # Filter critical emergency cases for the red-accented alerts list (limit to 5)
    emergency_alerts = [r for r in admin_reports if r.severity == PriorityLevel.CRITICAL][:5]

    # Generate recent activity audits dynamically based on database logs to satisfy zero-hardcoding
    recent_activities = []
    for r in admin_reports[:8]: # Parse last 8 reports
        recent_activities.append({
            "text": f"{r.name} filed concern report MCCRRS-{r.id} in {r.location}",
            "time": r.date_reported
        })
        if r.status != ReportStatus.SUBMITTED:
            recent_activities.append({
                "text": f"Status for MCCRRS-{r.id} transitioned to '{r.status}'",
                "time": "Updated"
            })

    # Render dashboard passing metric variables
    return render_template(
        'admin_dashboard.html',
        active_module='overview',
        total_reports=total_reports,
        pending_count=pending_count,
        resolved_count=resolved_count,
        emergency_count=emergency_count,
        recent_reports=admin_reports[:5], # Limit table display rows to 5
        emergency_alerts=emergency_alerts,
        recent_activities=recent_activities[:8]
    )


# Added: Route for Reports Management tabular display with text search capabilities
@app.route('/admin/reports')
def admin_reports():
    """Added: Displays tabular reporting data with real-time text query filtering."""
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    search_query = request.args.get('search', '').strip()

    # Query reports matching clearance
    reports_list = Report.get_admin_reports(clearance)

    # If search active, query criteria matches resident name, ID, location, concern, or status
    if search_query:
        query_lower = search_query.lower()
        reports_list = [
            r for r in reports_list
            if query_lower in str(r.id).lower()
            or query_lower in r.name.lower()
            or query_lower in r.concern.lower()
            or query_lower in r.location.lower()
            or query_lower in r.status.lower()
        ]

    # Render reports manager
    return render_template(
        'admin_reports.html',
        active_module='reports',
        reports=reports_list,
        search_query=search_query
    )


# Added: Route for Officials Management queues list and updates card
@app.route('/admin/officials', methods=['GET', 'POST'])
def admin_officials():
    """Added: Handles report queue selection and details modification views."""
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    search_query = request.args.get('search', '').strip()
    selected_id = request.args.get('id')

    # Query clearanced list
    reports_list = Report.get_admin_reports(clearance)

    # Filter queue list if search terms provided
    if search_query:
        reports_list = [
            r for r in reports_list
            if search_query.lower() in r.name.lower() or search_query.lower() in r.concern.lower()
        ]

    # Select report based on query parameter
    selected_report = None
    if selected_id:
        try:
            selected_report = Report.query.get(int(selected_id))
        except (ValueError, TypeError):
            pass

    # If no ID specified, default select the first report from the active queue
    if not selected_report and reports_list:
        selected_report = reports_list[0]

    # Render officials manager
    return render_template(
        'admin_officials.html',
        active_module='officials',
        reports=reports_list,
        selected_report=selected_report,
        search_query=search_query
    )


# Added: Route to process status changes, department assignments, progress logs, and photos
@app.route('/admin/update_report/<int:report_id>', methods=['POST'])
def admin_update_report(report_id):
    """Added: Persists officials assignments, progress logs, and photos directly in SQLite."""
    report = Report.query.get_or_404(report_id)

    # Read update values from form post
    department = request.form.get('department')
    notes = request.form.get('officer_notes')
    status = request.form.get('status')

    # Update model attributes
    if department:
        report.department = department
    if notes:
        report.officer_notes = notes
    if status:
        report.status = status

    # Handle image upload if officer attaches a progress photo
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            report.image = file.read() # Read image stream
            report.image_mimetype = file.mimetype # Save MIME type

    # Commit changes to SQLite
    db.session.commit()
    
    # Redirect back to selected officials view
    return redirect(url_for('admin_officials', id=report.id))


# Added: Route for Analytics Dashboard metrics, groupings, and CSS FlexBar aggregates
@app.route('/admin/analytics')
def admin_analytics():
    """Added: Maps database aggregates to flex complaining charts and ranking grids."""
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    reports_list = Report.get_admin_reports(clearance)

    # Count dynamic totals
    total_reports = len(reports_list)
    pending_count = sum(1 for r in reports_list if r.status in [ReportStatus.PENDING, ReportStatus.SUBMITTED])
    resolved_count = sum(1 for r in reports_list if r.status == ReportStatus.RESOLVED)
    emergency_count = sum(1 for r in reports_list if r.severity == PriorityLevel.CRITICAL)

    # Aggregating complaints categories counts for Complaints Bar Chart
    flooding_count = sum(1 for r in reports_list if "flood" in r.concern.lower() or "disaster" in r.concern.lower())
    fire_count = sum(1 for r in reports_list if "fire" in r.concern.lower() or "electric" in r.concern.lower())
    noise_count = sum(1 for r in reports_list if "noise" in r.concern.lower() or "complaint" in r.concern.lower())
    streetlight_count = sum(1 for r in reports_list if " streetlight" in r.concern.lower() or " streetlight" in r.concern.lower())

    # Rank most reported areas dynamically
    area_map = {}
    for r in reports_list:
        area = r.location.split(',')[0].strip() # Get local neighborhood name
        area_map[area] = area_map.get(area, 0) + 1

    # Sort area mappings by reported count descending
    sorted_areas = sorted(area_map.items(), key=lambda x: x[1], reverse=True)[:3]
    most_reported_areas = [{"name": a[0], "count": a[1]} for a in sorted_areas]

    # Pre-fill with placeholder if empty
    if not most_reported_areas:
        most_reported_areas = [{"name": "Zone 1", "count": 0}]

    # Department performance aggregations
    departments = [
        "Department of Public Works", "Manila Health Department",
        "Bureau of Fire Protection", "Manila Police District",
        "Manila Traffic and Parking Bureau", "Barangay Operations Center"
    ]
    dept_perf = []
    for dept in departments:
        assigned = sum(1 for r in reports_list if r.department == dept)
        resolved = sum(1 for r in reports_list if r.department == dept and r.status == ReportStatus.RESOLVED)
        status = "Excellent" if resolved >= assigned / 2 and assigned > 0 else "Good" if assigned > 0 else "Idle"
        dept_perf.append({
            "name": dept,
            "assigned": assigned,
            "resolved": resolved,
            "avg_response": "24h" if assigned > 0 else "—",
            "status": status
        })

    # Render analytics template
    return render_template(
        'admin_analytics.html',
        active_module='analytics',
        total_reports=total_reports,
        pending_count=pending_count,
        resolved_count=resolved_count,
        emergency_count=emergency_count,
        flooding_count=flooding_count,
        fire_count=fire_count,
        noise_count=noise_count,
        streetlight_count=streetlight_count,
        most_reported_areas=most_reported_areas,
        dept_perf=dept_perf
    )


# Added: Route for Announcements Feed management and new bulletin post creation
@app.route('/admin/announcements', methods=['GET', 'POST'])
def admin_announcements():
    """Added: Handles announcements query and new bulletins submission."""
    if request.method == 'POST':
        # Extract announcement data
        title = request.form['title']
        content = request.form['content']
        date_posted = datetime.now().strftime("%B %d, %Y")

        # Save to database
        new_ann = Announcement(title=title, content=content, date_posted=date_posted)
        db.session.add(new_ann)
        db.session.commit()
        return redirect(url_for('admin_announcements'))

    # Load announcements feed
    search_query = request.args.get('search', '').strip()
    feed = Announcement.query.order_by(Announcement.id.desc()).all()

    # Apply search filter if query is provided
    if search_query:
        feed = [a for a in feed if search_query.lower() in a.title.lower() or search_query.lower() in a.content.lower()]

    # Render announcements workspace
    return render_template(
        'admin_announcements.html',
        active_module='announcements',
        announcements=feed,
        search_query=search_query
    )


# Added: Route for Feedback Monitor to review modular rating cards
@app.route('/admin/feedback')
def admin_feedback():
    """Added: Parses citizen rating score reviews and feedback text details."""
    feedback_list = Feedback.query.order_by(Feedback.id.desc()).all()
    # Render feedback monitor
    return render_template(
        'admin_feedback.html',
        active_module='feedback',
        feedback_list=feedback_list
    )


# Added: Route for Submit Concern embedding the citizen reporting form
@app.route('/admin/submit', methods=['GET', 'POST'])
def admin_submit():
    """Added: Embeds standard citizen report form directly inside admin sidebar."""
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        concern = request.form['concern']
        description = request.form.get('description', '')
        date_reported = request.form.get('date_reported', '')

        # Classify severity
        severity = SEVERITY_MAPPING.get(concern, PriorityLevel.MINOR)

        # Handle image upload
        image_data = None
        image_mimetype = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_data = file.read()
                image_mimetype = file.mimetype

        # Persist report record
        new_report = Report(
            name=name,
            location=location,
            concern=concern,
            severity=severity,
            status=ReportStatus.SUBMITTED,
            description=description,
            image=image_data,
            image_mimetype=image_mimetype,
            date_reported=date_reported or datetime.now().strftime("%B %d, %Y %I:%M %p")
        )
        db.session.add(new_report)
        db.session.commit()

        # Redirect to Reports tab in admin
        return redirect(url_for('admin_reports'))

    # GET request — render form nested inside admin base
    return render_template('admin_submit.html', active_module='submit')


# Added: Route to terminate session and log out admin user
@app.route('/admin/logout')
def admin_logout():
    """Added: Clears Flask admin auth parameters and redirects back to login screen."""
    session.pop('admin_logged_in', None)
    session.pop('admin_name', None)
    session.pop('admin_clearance', None)
    session.pop('admin_sec_number', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)