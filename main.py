#CourseProject _ Group 8 _OOP
"Title of the Project: Manila Community Concern Reporting and Response System"
"""Project Manager - Leia Naomi Novales
UI/UX - Anika Almonia
QA Testing - Carelle Jumao-As
Software Engineer - Francheska Allan
Software Engineer - Archie Gujilde
Software Engineer - Josh Brian Las-Marias"""



class User: # tentative
    def __init__(self, user_type):
        self.user_type = user_type

class Resident(User):
    def __init__(self):
        super().__init__("Resident")
        
