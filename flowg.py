print("Select User Type: Resident or Admin")
userType = input()
if userType == "Resident":
    print("What's your Concern?")
    concern = input()
    print("What is the severity of the concern? (Minor, Major, Critical)")
    severity = input().lower()
    if severity == "minor":
        print("Barangay Hotline : (02) 0000 - 0000")
        print("City Hall: 234-5678")
    else:
        if severity == "Major":
            print("Police Non-Emergency: 345-6789")
            print("Fire Department (Sta. Mesa):(02) 8716-1634 or 0917-834-0309")
        else:
            if severity == "Critical":
                print("Contact this Immediately")
                print("National Emergency Hotline: 911")
                print("NDRRMC: (02) 8911-5061 to 65 (local 100), (02) 8911-1406, (02) 8912-2665, (02) 8912-5668, and (02) 8911-1873")
                print("Manila City Hall (Disaster Risk Reduction): (02) 8527-5174")
                print("Manila Fire District HQ: (02) 8527-3604 / (02) 8527-3606")
    print("Concern submitted to Government Officials")
else:
    if userType == "Admin":
        print("Admin Login Portal")
        print("Enter Name:")
        adminName = input()
        print("Enter Password:")
        adminPassword = input()
        print("Enter Security Number:")
        securityNumber = input()
        validLogin = False
        if securityNumber == "11111A":
            tier = "Minor"
            validLogin = True
        else:
            if securityNumber == "12121B":
                tier = "Major"
                validLogin = True
            else:
                if securityNumber == "13131C":
                    tier = "Critical"
                    validLogin = True
        if validLogin == True:
            print("Login Successful! Access Granted")
            print("Viewing " + tier + " Concerns arranged by time reported")
            print("Admin can update status: Resolved, Unresolved, Ongoing, or Reported")
        else:
            print("Login Failed! Invalid Credentials")
    else:
        print("Invalid User Type")
