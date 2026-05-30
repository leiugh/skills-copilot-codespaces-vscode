"Title of the Project: Manila Community Concern Reporting and Response System"
"""Project Manager - Leia Naomi Novales
UI/UX - Anika Almonia
QA Testing - Carelle Jumao-As
Software Engineer - Francheska Allan
Software Engineer - Archie Gujilde
Software Engineer - Brian Josh Las Marias"""

from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy #database
from abc import ABC, abstractmethod
from datetime import datetime 
import os


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

class PriorityLevel:
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


class ReportStatus:
    SUBMITTED = "Submitted"
    REVIEWED = "Reviewed"
    ASSIGNED = "Assigned"
    PENDING = "Pending"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"

# SQLALCHEMY REPORT MODEL & ENCAPSULATION METHODS

class Report(db.Model):
    """SQLAlchemy model representing a submitted community concern report."""
    __tablename__ = 'reports'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(120), nullable=False)
    location       = db.Column(db.String(200), nullable=False)
    concern        = db.Column(db.Text, nullable=False)
    severity       = db.Column(db.String(20), nullable=False)
    status         = db.Column(db.String(30), nullable=False, default=ReportStatus.PENDING)
    description    = db.Column(db.Text, nullable=True)
    image          = db.Column(db.LargeBinary, nullable=True)
    image_mimetype = db.Column(db.String(50), nullable=True)
    date_reported  = db.Column(db.String(50), nullable=True)
    department     = db.Column(db.String(100), nullable=True)
    officer_notes  = db.Column(db.Text, nullable=True)

    def __init__(self, name, location, concern, severity, status=None, description=None, image=None, image_mimetype=None, date_reported=None, department=None, officer_notes=None, id=None):
        """Explicit constructor to satisfy static IDE type analyzers (e.g. Pyright/Pylance)."""
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
        return self.department or "Pending Assignment"

    @officer_assignment.setter
    def officer_assignment(self, value):
        self.department = value

    @classmethod
    def get_public_reports(cls):
        return cls.query.order_by(cls.id.desc()).all()

    @classmethod
    def get_admin_reports(cls, clearance):
        """Fetches report records dynamically filtered by security clearance level."""
        if clearance == PriorityLevel.CRITICAL:
            return cls.query.order_by(cls.id.desc()).all()
        elif clearance == PriorityLevel.MAJOR:
            return cls.query.filter(cls.severity.in_([PriorityLevel.MINOR, PriorityLevel.MAJOR])).order_by(cls.id.desc()).all()
        else:
            return cls.query.filter(cls.severity == PriorityLevel.MINOR).order_by(cls.id.desc()).all()

    @classmethod
    def get_stats(cls, clearance):
        """Encapsulates dashboard stats calculation."""
        reps = cls.get_admin_reports(clearance)
        total = len(reps)
        pending = sum(1 for r in reps if r.status in [ReportStatus.PENDING, ReportStatus.SUBMITTED])
        resolved = sum(1 for r in reps if r.status == ReportStatus.RESOLVED)
        emergency = sum(1 for r in reps if r.severity == PriorityLevel.CRITICAL)
        return total, pending, resolved, emergency

    @classmethod
    def get_analytics(cls, clearance):
        """Encapsulates database aggregates and department analytics."""
        reps = cls.get_admin_reports(clearance)
        flooding = sum(1 for r in reps if "flood" in r.concern.lower() or "disaster" in r.concern.lower())
        fire = sum(1 for r in reps if "fire" in r.concern.lower() or "electric" in r.concern.lower())
        noise = sum(1 for r in reps if "noise" in r.concern.lower() or "complaint" in r.concern.lower())
        streetlight = sum(1 for r in reps if "streetlight" in r.concern.lower())

        area_map = {}
        for r in reps:
            area = r.location.split(',')[0].strip()
            area_map[area] = area_map.get(area, 0) + 1
        sorted_areas = sorted(area_map.items(), key=lambda x: x[1], reverse=True)[:3]
        most_reported = [{"name": a[0], "count": a[1]} for a in sorted_areas] or [{"name": "Zone 1", "count": 0}]

        departments = [
            "Department of Public Works", "Manila Health Department",
            "Bureau of Fire Protection", "Manila Police District",
            "Manila Traffic and Parking Bureau", "Barangay Operations Center"
        ]
        dept_perf = []
        for dept in departments:
            assigned = sum(1 for r in reps if r.department == dept)
            resolved = sum(1 for r in reps if r.department == dept and r.status == ReportStatus.RESOLVED)
            status = "Excellent" if resolved >= assigned / 2 and assigned > 0 else "Good" if assigned > 0 else "Idle"
            dept_perf.append({
                "name": dept,
                "assigned": assigned,
                "resolved": resolved,
                "avg_response": "24h" if assigned > 0 else "—",
                "status": status
            })
        return len(reps), flooding, fire, noise, streetlight, most_reported, dept_perf

    @classmethod
    def submit_report(cls, name, location, concern, description, date_reported, image_file=None):
        """Encapsulates report validation, creation, and persistent storage."""
        severity = SEVERITY_MAPPING.get(concern, PriorityLevel.MINOR)
        
        # OOP Resident validation check
        resident_user = Resident(name, location)
        resident_user.report_concern(concern, severity)

        image_data = None
        image_mimetype = None
        if image_file and image_file.filename != '':
            image_data = image_file.read()
            image_mimetype = image_file.mimetype

        is_empty = (cls.query.count() == 0)
        new_report = cls(
            id=1001 if is_empty else None,
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

        # OOP legacy array compatibility
        report_system = ReportSystem(name, location, concern, severity)
        reports.append(report_system)
        return new_report

    def update_details(self, department, notes, status, image_file=None):
        """Encapsulates administrative queue update and notes submission logic."""
        if department:
            self.department = department
        if notes:
            self.officer_notes = notes
        if status:
            self.status = status
        if image_file and image_file.filename != '':
            self.image = image_file.read()
            self.image_mimetype = image_file.mimetype
        db.session.commit()

    def __repr__(self):
        return f"<Report {self.id} | {self.severity} | {self.status}>"


class Announcement(db.Model):
    """SQLAlchemy model representing a published city announcement bulletin."""
    __tablename__ = 'announcements'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(200), nullable=False)
    date_posted    = db.Column(db.String(50), nullable=False)
    content        = db.Column(db.Text, nullable=False)
    image          = db.Column(db.LargeBinary, nullable=True)
    image_mimetype = db.Column(db.String(50), nullable=True)


class Feedback(db.Model):
    """SQLAlchemy model representing feedback details submitted by citizens on resolved concerns."""
    __tablename__ = 'feedback'

    id                  = db.Column(db.Integer, primary_key=True)
    citizen_name        = db.Column(db.String(120), nullable=False)
    concern_category    = db.Column(db.String(120), nullable=False)
    department_assigned = db.Column(db.String(120), nullable=True)
    rating              = db.Column(db.Integer, nullable=False)
    comment             = db.Column(db.Text, nullable=True)
    date_submitted      = db.Column(db.String(50), nullable=False)

    def __init__(self, citizen_name, concern_category, rating, comment, date_submitted, department_assigned=None, id=None):
        """Explicit constructor to satisfy static IDE type analyzers (e.g. Pyright/Pylance)."""
        if id is not None:
            self.id = id
        self.citizen_name = citizen_name
        self.concern_category = concern_category
        self.department_assigned = department_assigned
        self.rating = rating
        self.comment = comment
        self.date_submitted = date_submitted

class User(ABC):
    def __init__(self, user_type, name, location):
        self.user_type = user_type
        self.name = name
        self.location = location

    @abstractmethod
    def report_concern(self):
        pass


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

    def display_hotlines(self) -> None:
        if self.severity is None:
            raise RuntimeError("No concern report detected. Please try again.")
        if self.severity == PriorityLevel.MINOR:
            print("Contact: Barangay Hotline: (02) 0000-0000\nCity Hall: 234-5678")
        elif self.severity == PriorityLevel.MAJOR:
            print("Contact: Police Non Emergency: 345-6789\nFire Department: (02) 8716-1634")
        elif self.severity == PriorityLevel.CRITICAL:
            print("Contact: NDRRMC: (02) 8911-5506\nNational Hotline: 911")


class Admin(User):
    # Fully Encapsulated Private Map (Security Clearance Tiers)
    _sec_number_map = {"11111A": PriorityLevel.MINOR, "12121B": PriorityLevel.MAJOR, "13131C": PriorityLevel.CRITICAL}

    def __init__(self, name, password, sec_number):
        super().__init__("Admin", name, "City Hall")
        self.name = name
        self.__password = password  # Encapsulated private attribute

        if sec_number not in self._sec_number_map:
            raise ValueError(f"Access Denied. Invalid Security Number: {sec_number}.")
        self.sec_number = sec_number
        self.valid_login = False

    def login(self, input_password: str) -> bool:
        """Securely verifies encapsulated credential inputs."""
        if self.__password == input_password:
            self.valid_login = True
            return True
        return False

    @classmethod
    def get_clearance_by_sec_number(cls, sec_number):
        """Secure getter encapsulation for security clearance mapping."""
        return cls._sec_number_map.get(sec_number, PriorityLevel.MINOR)

    def _require_authentication(self):
        if not self.valid_login:
            raise PermissionError("You must be logged in first.")

    def report_concern(self) -> tuple[str, str]:
        self._require_authentication()
        concern = input("Admin concern: ")
        severity = input("Severity: ")
        if severity not in {PriorityLevel.MINOR, PriorityLevel.MAJOR, PriorityLevel.CRITICAL}:
            raise ValueError("Unsupported Severity.")
        return concern, severity


class ReportIDGenerator:
    current_id = 1000

    @classmethod
    def generate_id(cls):
        cls.current_id += 1
        return f"MCCRRS-{cls.current_id}"


class ReportSystem:
    def __init__(self, name, location, concern, severity):
        self.report_id = ReportIDGenerator.generate_id()
        self.name = name
        self.location = location
        self.concern = concern
        self.severity = severity
        self.status = ReportStatus.PENDING
        self.date_reported = datetime.now().strftime("%B %d, %Y %I:%M %p")

    def update_status(self, new_status) -> None:
        if new_status not in (ReportStatus.SUBMITTED, ReportStatus.REVIEWED, ReportStatus.ASSIGNED, ReportStatus.PENDING, ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED, ReportStatus.REJECTED):
            raise ValueError("Invalid Status.")
        self.status = new_status

    def assign_report(self, admin: Admin) -> None:
        if not admin.valid_login:
            raise PermissionError("Admin must be logged in.")
        self.status = ReportStatus.ASSIGNED

    def display_report(self) -> None:
        print(f"Reference No.: {self.report_id}\nName: {self.name}\nLocation: {self.location}\nConcern: {self.concern}\nSeverity: {self.severity}\nDate: {self.date_reported}\nStatus: {self.status}")


reports = []

# DATABASE INITIALIZATION
with app.app_context():
    try:
        db.create_all()
        if Announcement.query.count() == 0:
            db.session.add(Announcement(id=1, title="Typhoon Preparedness Advisory", date_posted="May 28, 2026", content="Signal No. 2 declared for Metro Manila due to approaching Typhoon. Expect heavy rainfall and moderate to strong winds. Secure loose objects and keep emergency kits prepared."))
            db.session.add(Announcement(id=2, title="Manila City Hall Health Caravan", date_posted="May 29, 2026", content="Free comprehensive public health caravan at the Sta. Ana Health Center. Free check-ups, dental extraction, vaccine shots, and priority queue given to seniors and infants."))
            db.session.add(Announcement(id=3, title="Garbage Collection Delay", date_posted="May 30, 2026", content="Garbage collection will resume tomorrow due to scheduled truck maintenance operations in selective districts."))
            db.session.commit()

        if Feedback.query.count() == 0:
            db.session.add(Feedback(citizen_name="Juan Cruz", concern_category="Large Potholes", department_assigned="Department of Public Works", rating=5, comment="Pothole filled within 48 hours of my report! Amazing responsiveness.", date_submitted="May 30, 2026 03:00 PM"))
            db.session.add(Feedback(citizen_name="Mami Oni", concern_category="Electrical Fire or Exposed Live Wires", department_assigned="Bureau of Fire Protection", rating=4, comment="BFP responded immediately to secure the smoking pole. Excellent coordination.", date_submitted="May 30, 2026 04:30 PM"))
            db.session.add(Feedback(citizen_name="Pedro Penduko", concern_category="Noise Complaint", department_assigned="Manila Police District", rating=2, comment="Response took too long and the neighbors just turned up the noise again later.", date_submitted="May 31, 2026 01:15 AM"))
            db.session.add(Feedback(citizen_name="Mami Oni", concern_category="letche di naman nila ni resolve", rating=1, comment="Response took too long and the neighbors just turned up the noise again later.", date_submitted="May 31, 2026 01:15 AM"))
            db.session.commit()
    except Exception as e:
        print(f"Database initialization alert: {e}")


# SEVERITY CLASSIFICATION MAPPING para sa automatic severity assignment base sa concern category. This is used in the Report.submit_report() method to determine the severity level of a report based on its concern category.

SEVERITY_MAPPING = {
    "Fire Incident": PriorityLevel.CRITICAL,
    "Flooding or Natural Disaster": PriorityLevel.CRITICAL,
    "Ongoing Crime (Robbery/Assault/Violence)": PriorityLevel.CRITICAL,
    "Medical Emergency": PriorityLevel.CRITICAL,
    "Gas Leak": PriorityLevel.CRITICAL,
    "Electrical Fire or Exposed Live Wires": PriorityLevel.CRITICAL,
    "Missing Person": PriorityLevel.CRITICAL,
    "Building/House Collapse": PriorityLevel.CRITICAL,
    "Road Accident": PriorityLevel.CRITICAL,

    "Large Potholes": PriorityLevel.MAJOR,
    "Water Interruption in the Community": PriorityLevel.MAJOR,
    "Power Outage": PriorityLevel.MAJOR,
    "Illegal Dumping of Garbage": PriorityLevel.MAJOR,
    "Damaged Drainage System": PriorityLevel.MAJOR,
    "Noise Complaint": PriorityLevel.MAJOR,
    "Broken Streetlight": PriorityLevel.MAJOR,

    "Small Potholes": PriorityLevel.MINOR,
    "Graffiti / Vandalism": PriorityLevel.MINOR,
    "Overgrown Grass / Plants": PriorityLevel.MINOR,
    "Minor Noise Complaint": PriorityLevel.MINOR,
    "Broken Bench or Public Use": PriorityLevel.MINOR,
    "Request for Additional Bins": PriorityLevel.MINOR,
    "Minor Sidewalk Crack": PriorityLevel.MINOR
}
# FLASK ROUTES dito inimport yung styling at templates, and dito flow to submit ng report, pag view ng report status, at admin dashboard yung asa gilid.

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html', active_page='home')


@app.route('/about')
def about():
    return render_template('about.html', active_page='about')


@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        new_report = Report.submit_report(
            request.form['name'],
            request.form['location'],
            request.form['concern'],
            request.form.get('description', ''),
            request.form.get('date_reported', ''),
            request.files.get('image')
        )
        return redirect(url_for('track', id=new_report.id))
    return render_template('report.html', active_page='report')


@app.route('/resident', methods=['GET', 'POST'])
def resident():
    return redirect(url_for('report'))


@app.route('/track')
def track():
    report_id_str = request.args.get('id')
    report = None
    if report_id_str:
        clean_id = report_id_str.replace("MCCRRS-", "").strip()
        try:
            report = Report.query.get(int(clean_id))
        except (ValueError, TypeError):
            pass
    if not report:
        report = Report.query.order_by(Report.id.desc()).first()

    progress = 20
    if report:
        if report.status in [ReportStatus.SUBMITTED, ReportStatus.PENDING]:
            progress = 20
        elif report.status == ReportStatus.REVIEWED:
            progress = 40
        elif report.status == ReportStatus.ASSIGNED:
            progress = 60
        elif report.status == ReportStatus.IN_PROGRESS:
            progress = 80
        elif report.status == ReportStatus.RESOLVED:
            progress = 100
    return render_template('track.html', report=report, progress_percentage=progress, active_page='track')


@app.route('/announcements')
def announcements():
    return render_template('announcements.html', active_page='announcements')


@app.before_request
def admin_auth_guard():
    if request.path.startswith('/admin') and request.path not in ['/admin/login', '/admin']:
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))


@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_login'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        sec_number = request.form.get('sec_number', '')
        try:
            admin_user = Admin(email, password, sec_number)
            if admin_user.login(password):
                session['admin_logged_in'] = True
                session['admin_name'] = email.split('@')[0].capitalize()
                session['admin_clearance'] = Admin.get_clearance_by_sec_number(sec_number)
                session['admin_sec_number'] = sec_number
                return redirect(url_for('admin_dashboard'))
            return render_template('admin_login.html', error="Invalid password. Please try again.")
        except ValueError as e:
            return render_template('admin_login.html', error=str(e))
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    reps = Report.get_admin_reports(clearance)
    tot, pend, res, emerg = Report.get_stats(clearance)

    activities = []
    for r in reps[:8]:
        activities.append({"text": f"{r.name} filed concern report MCCRRS-{r.id} in {r.location}", "time": r.date_reported})
        if r.status != ReportStatus.SUBMITTED:
            activities.append({"text": f"Status for MCCRRS-{r.id} transitioned to '{r.status}'", "time": "Updated"})

    return render_template(
        'admin_dashboard.html',
        active_module='overview',
        total_reports=tot,
        pending_count=pend,
        resolved_count=res,
        emergency_count=emerg,
        recent_reports=reps[:5],
        emergency_alerts=[r for r in reps if r.severity == PriorityLevel.CRITICAL][:5],
        recent_activities=activities[:8]
    )


@app.route('/admin/reports')
def admin_reports():
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    search_query = request.args.get('search', '').strip()
    reps = Report.get_admin_reports(clearance)

    if search_query:
        ql = search_query.lower()
        reps = [r for r in reps if ql in str(r.id).lower() or ql in r.name.lower() or ql in r.concern.lower() or ql in r.location.lower() or ql in r.status.lower()]

    return render_template('admin_reports.html', active_module='reports', reports=reps, search_query=search_query)


@app.route('/admin/officials', methods=['GET', 'POST'])
def admin_officials():
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    search_query = request.args.get('search', '').strip()
    selected_id = request.args.get('id')
    reps = Report.get_admin_reports(clearance)

    if search_query:
        reps = [r for r in reps if search_query.lower() in r.name.lower() or search_query.lower() in r.concern.lower()]

    selected_report = None
    if selected_id:
        try:
            selected_report = Report.query.get(int(selected_id))
        except (ValueError, TypeError):
            pass
    if not selected_report and reps:
        selected_report = reps[0]

    return render_template('admin_officials.html', active_module='officials', reports=reps, selected_report=selected_report, search_query=search_query)


@app.route('/admin/update_report/<int:report_id>', methods=['POST'])
def admin_update_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.update_details(
        request.form.get('department'),
        request.form.get('officer_notes'),
        request.form.get('status'),
        request.files.get('image')
    )
    return redirect(url_for('admin_officials', id=report.id))


@app.route('/admin/analytics')
def admin_analytics():
    clearance = session.get('admin_clearance', PriorityLevel.MINOR)
    tot, flooding, fire, noise, streetlight, most_reported, dept_perf = Report.get_analytics(clearance)
    tot, pend, res, emerg = Report.get_stats(clearance)
    return render_template(
        'admin_analytics.html',
        active_module='analytics',
        total_reports=tot,
        pending_count=pend,
        resolved_count=res,
        emergency_count=emerg,
        flooding_count=flooding,
        fire_count=fire,
        noise_count=noise,
        streetlight_count=streetlight,
        most_reported_areas=most_reported,
        dept_perf=dept_perf
    )


@app.route('/admin/announcements', methods=['GET', 'POST'])
def admin_announcements():
    if request.method == 'POST':
        new_ann = Announcement(title=request.form['title'], content=request.form['content'], date_posted=datetime.now().strftime("%B %d, %Y"))
        db.session.add(new_ann)
        db.session.commit()
        return redirect(url_for('admin_announcements'))

    search_query = request.args.get('search', '').strip()
    feed = Announcement.query.order_by(Announcement.id.desc()).all()
    if search_query:
        feed = [a for a in feed if search_query.lower() in a.title.lower() or search_query.lower() in a.content.lower()]

    return render_template('admin_announcements.html', active_module='announcements', announcements=feed, search_query=search_query)


@app.route('/admin/feedback')
def admin_feedback():
    return render_template('admin_feedback.html', active_module='feedback', feedback_list=Feedback.query.order_by(Feedback.id.desc()).all())


@app.route('/admin/submit', methods=['GET', 'POST'])
def admin_submit():
    if request.method == 'POST':
        Report.submit_report(
            request.form['name'],
            request.form['location'],
            request.form['concern'],
            request.form.get('description', ''),
            request.form.get('date_reported', ''),
            request.files.get('image')
        )
        return redirect(url_for('admin_reports'))
    return render_template('admin_submit.html', active_module='submit')


@app.route('/admin/logout')
def admin_logout():
    for key in ['admin_logged_in', 'admin_name', 'admin_clearance', 'admin_sec_number']:
        session.pop(key, None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)