#CourseProject _ Group 8 _OOP
"Title of the Project: Manila Community Concern Reporting and Response System"
"""Project Manager - Leia Naomi Novales
UI/UX - Anika Almonia
QA Testing - Carelle Jumao-As
Software Engineer - Francheska Allan
Software Engineer - Archie Gujilde
Software Engineer - Josh Brian Las-Marias"""

#Priority
class PriorityLevel:
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"

#Status of the Report
class ReportStatus:
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"

# Parent Class
class User: # tentative
    def __init__(self, user_type):
        self.user_type = user_type

class Resident(User): 
    def __init__(self, concern = "", severity = ""):
        super().__init__("Resident")
        self.concern = concern 
        self.severity = severity
    
    def report_concern(self):
        pass

class Admin(User):
    #Encapsulation Private (Security Numbers)
    _sec_number_map = {"11111A": PriorityLevel.MINOR, "12121B": PriorityLevel.MAJOR, "13131C": PriorityLevel.CRITICAL}

    def __init__(self, name, password, sec_number):
        super().__init__("Admin")
        self.name = name
        self.password = password
        self.sec_number = sec_number
        self.valid_login = False

    def login (self, input_password: str) -> bool:
        if self.password == input_password:
            self.valid_login = True
            clearance_level = self._sec_number_map.get(self.sec_number, PriorityLevel.MINOR)
            print (f"Sucessful Login. \nAdmin : |{self.name}|\nSecurity Clearance: |{clearance_level}| ")
            return True
        print (f"Invalid Login.")
        return False    
    
    def _require_authentication (self): # validation for login 
        if not self.valid_login:
            raise PermissionError ("You must be logged in first.") #ExceptionError
    
# Report System Class 
class ReportSystem:
    def __init__(self, report_id, location, concern, severity):
        self.report_id = report_id
        self.location = location
        self.concern = concern 
        self.severity = severity 
        self.status = ReportStatus.PENDING

    def update_status(self, new_status) -> str:
        if new_status in (ReportStatus.SUBMITTED, ReportStatus.REVIEWED, ReportStatus.ASSIGFNED, ReportStatus.PENDING, ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED, ReportStatus.REJECTED):
            self.status = new_status
            print(f"Report ID: {self.report_id} status updated to {self.status}.")
        else:
            print("invalid status update. Please choose a valid status.")
    
    def assign_report(self, admin: Admin) -> str:
        if admin.valid_login:
            self.status = ReportStatus.ASSIGNED
            print(f"Report ID: {self.report_id} has been assigned to Admin: {admin.name}.")
        else:
            print("Admin must be logged in to assign the report.")
                

    def display_report(self):
        print(f"Reference No.: {self.report_id}")
        print(f"name: {self.name}")
        print(f"location: {self.location}")
        print(f"Concern: {self.concern}")
        print(f"Severity: {self.severity}")
        print(f"Status: {self.status}")

# Global Storage for Reports
reports = []