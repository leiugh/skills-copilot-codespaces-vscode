#CourseProject _ Group 8 _OOP
"Title of the Project: Manila Community Concern Reporting and Response System"
"""Project Manager - Leia Naomi Novales
UI/UX - Anika Almonia
QA Testing - Carelle Jumao-As
Software Engineer - Francheska Allan
Software Engineer - Archie Gujilde
Software Engineer - Brian Josh Las Marias"""

from flask import Flask, render_template, request, redirect
from abc import ABC, abstractmethod
from datetime import datetime

app = Flask(__name__)

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

@app.route('/')
def home ():
    return render_template('index.html')

@app.route('/resident', methods=['GET', 'POST'])
def resident():

    if request.method == 'POST':

        name = request.form['name']
        location = request.form['location']
        concern = request.form['concern']
        severity = request.form['severity']

        resident_user = Resident(name, location)
        resident_user.report_concern(concern, severity)

        report = ReportSystem(ReportIDGenerator.generate_id(), name, location, concern, severity)

        reports.append(report)

        return render_template('success.html',
            name=name,
            severity=severity
            )

    return render_template('resident.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/reports')
def view_reports():
    return render_template('reports.html', reports=reports)


if __name__ == '__main__':
    app.run(debug=True)

    