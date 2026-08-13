import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from auth import hash_password, verify_password
from db import ConfigRecord, TemplateRecord, UserRecord, VariableRecord
from library_seed import SEED_TIMESTAMP, build_library_templates, build_variables as build_library_variables

NOTICE_CATEGORIES = ["Security", "Infrastructure", "IT", "HR", "Facilities", "Projects", "Management", "Support"]

MASTER_DATA_KEY = "master-data"
LIBRARY_IMPORT_KEY = "library-import-v2"
PASSWORD_RESET_KEY = "password-resets"


def get_manual_password_resets(db: Session) -> set:
    """Emails whose password was manually reset by an admin. The startup demo
    password sync must not overwrite these."""
    record = db.query(ConfigRecord).filter(ConfigRecord.key == PASSWORD_RESET_KEY).first()
    if not record:
        return set()
    return set(record.payload.get("emails", []))


def mark_password_reset(db: Session, email: str):
    record = db.query(ConfigRecord).filter(ConfigRecord.key == PASSWORD_RESET_KEY).first()
    if not record:
        record = ConfigRecord(key=PASSWORD_RESET_KEY, payload={"emails": []})
        db.add(record)
    if email not in record.payload["emails"]:
        # Re-assign the attribute (not in-place list append): SQLAlchemy does not
        # track mutations inside JSON columns, so an in-place append would be
        # silently lost on commit and the marker would never persist past the
        # first email.
        record.payload = {
            **record.payload,
            "emails": [*record.payload["emails"], email],
        }
    db.commit()

VAR_NAME_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def _item(name, **extra):
    return {"id": str(uuid.uuid4()), "name": name, "active": True, **extra}


def build_master_data():
    category_names = [
        "Client Communication", "Meeting Minutes", "Checklists", "Announcements", "Policies", "Events",
        "Recruitment", "Business Documents", "Employee Announcements"
    ] + NOTICE_CATEGORIES

    return {
        "updatedBy": "System",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "lists": {
            "categories": {
                "items": [_item(name, parentId=None) for name in category_names],
            },
            "departments": {
                "items": [_item(name) for name in ["HR", "Engineering", "Sales", "Finance", "IT"]],
            },
            "languages": {
                "items": [_item(name) for name in [
                    "English", "Hindi", "Spanish", "French", "German", "Portuguese", "Italian", "Dutch",
                    "Arabic", "Russian", "Chinese (Simplified)", "Japanese", "Korean", "Vietnamese",
                    "Tamil", "Telugu", "Bengali", "Marathi", "Gujarati", "Kannada",
                ]],
                "default": "English",
            },
            "priorities": {
                "items": [
                    {"id": str(uuid.uuid4()), "name": "Critical", "active": True, "order": 0, "badgeClass": "badge-danger", "description": "Urgent, time-sensitive", "requiresAcknowledgementDefault": True},
                    {"id": str(uuid.uuid4()), "name": "High", "active": True, "order": 1, "badgeClass": "badge-warning", "description": "Important, needs prompt attention", "requiresAcknowledgementDefault": False},
                    {"id": str(uuid.uuid4()), "name": "Normal", "active": True, "order": 2, "badgeClass": "badge-neutral", "description": "Standard priority", "requiresAcknowledgementDefault": False},
                    {"id": str(uuid.uuid4()), "name": "Low", "active": True, "order": 3, "badgeClass": "badge-neutral", "description": "No urgency", "requiresAcknowledgementDefault": False},
                ],
            },
        },
    }


def get_default_sections():
    return [
        {"id": "s1", "name": "Participants", "type": "PeoplePicker", "enabled": True, "order": 1, "required": True, "defaultContent": ["Name", "Role", "Organization", "Attendance"]},
        {"id": "s2", "name": "Agenda", "type": "RichText", "enabled": True, "order": 2, "required": True, "defaultContent": "1. \n2. \n3. "},
        {"id": "s3", "name": "Discussion", "type": "RichText", "enabled": True, "order": 3, "required": False, "defaultContent": "<strong>Key Points:</strong><br><br><strong>Questions:</strong>"},
        {"id": "s4", "name": "Decisions", "type": "Table", "enabled": True, "order": 4, "required": False, "defaultContent": ["Decision", "Decision By", "Decision Date"]},
        {"id": "s5", "name": "Action Items", "type": "Table", "enabled": True, "order": 5, "required": False, "defaultContent": ["Task", "Owner", "Priority", "Due Date", "Status"]}
    ]


def get_default_checklist_items():
    return [
        {"id": "c1", "title": "Verify Environment Variables", "description": "Check if production env vars are set correctly", "mandatory": True, "ownerRole": "DevOps", "evidenceRequired": False},
        {"id": "c2", "title": "Run Security Scan", "description": "Ensure no high vulnerabilities via SonarQube", "mandatory": True, "ownerRole": "QA", "evidenceRequired": True},
        {"id": "c3", "title": "Notify Client", "description": "Send deployment notification", "mandatory": False, "ownerRole": "Manager", "evidenceRequired": False},
    ]


def get_default_event_trigger():
    return {
        "enabled": False,
        "eventType": "Birthday",
        "autoGenerate": False,
        "autoPublish": False,
        "leadTimeDays": 0
    }


def get_default_publishing():
    return {
        "priority": "Normal",
        "publishImmediately": True,
        "effectiveDate": "",
        "expiryDate": "",
        "audience": {
            "allEmployees": True,
            "departments": [],
            "locations": [],
            "roles": []
        },
        "notificationBehavior": {
            "requireAcknowledgement": False,
            "allowComments": True
        }
    }


def build_variables():
    return [
        {"id": "v1", "name": "ClientName", "display_name": "Client Name", "type": "String", "category": "Client", "required": True, "default_value": "ABC Pvt Ltd", "description": "Displays client's official name"},
        {"id": "v2", "name": "ProjectName", "display_name": "Project Name", "type": "String", "category": "Project", "required": True, "default_value": "Project Phoenix", "description": "The name of the project"},
        {"id": "v3", "name": "EmployeeName", "display_name": "Employee Name", "type": "String", "category": "Employee", "required": True, "default_value": "John Doe", "description": "Assigned employee name"},
        {"id": "v4", "name": "Employee", "display_name": "Employee", "type": "String", "category": "Employee Announcements", "required": True, "default_value": "Priya Sharma", "description": "Employee the announcement is about"},
        {"id": "v5", "name": "Department", "display_name": "Department", "type": "String", "category": "Employee Announcements", "required": True, "default_value": "Engineering", "description": "Employee's department"},
        {"id": "v6", "name": "Years", "display_name": "Years", "type": "Number", "category": "Employee Announcements", "required": False, "default_value": "5", "description": "Years of service, used for anniversaries"},
        {"id": "v7", "name": "Photo", "display_name": "Photo", "type": "Image", "category": "Employee Announcements", "required": False, "default_value": "https://i.pravatar.cc/150?img=12", "description": "Employee's photo"},
        {"id": "v8", "name": "Manager", "display_name": "Manager", "type": "String", "category": "Employee Announcements", "required": False, "default_value": "Rahul Verma", "description": "Employee's manager or reporting lead"},
        {"id": "v9", "name": "Quote", "display_name": "Quote", "type": "String", "category": "Employee Announcements", "required": False, "default_value": "Success is the sum of small efforts, repeated day in and day out.", "description": "A congratulatory or motivational quote"},
        {"id": "v10", "name": "InvoiceNumber", "display_name": "Invoice Number", "type": "String", "category": "Business Documents", "required": True, "default_value": "INV-2026-0142", "description": "Unique invoice or purchase order number"},
        {"id": "v11", "name": "Amount", "display_name": "Amount", "type": "String", "category": "Business Documents", "required": True, "default_value": "$4,500.00", "description": "Formatted total amount due"},
        {"id": "v12", "name": "DueDate", "display_name": "Due Date", "type": "Date", "category": "Business Documents", "required": False, "default_value": "2026-09-15", "description": "Payment or response due date"},
        {"id": "v13", "name": "CandidateName", "display_name": "Candidate Name", "type": "String", "category": "Business Documents", "required": True, "default_value": "Aditi Rao", "description": "Name of the job candidate"},
        {"id": "v14", "name": "JobTitle", "display_name": "Job Title", "type": "String", "category": "Business Documents", "required": True, "default_value": "Senior Software Engineer", "description": "Job title being offered or referenced"},
    ]


def build_templates():
    templates = [
        {
            "id": "1",
            "name": "Welcome Client",
            "description": "Onboarding communication for new clients.",
            "department": "Sales",
            "category": "Client Communication",
            "tags": ["onboarding", "welcome"],
            "status": "Published",
            "owner": "Sales Admin",
            "created_by": "Sales Admin",
            "updated_by": "Sales Admin",
            "version": 1,
            "language": "English",
            "visibility": "Public",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": True,
                "footerEnabled": True,
                "letterheadEnabled": False,
                "companyDetailsEnabled": True
            },
            "channels": {
                "email": {
                    "enabled": True,
                    "subject": "Welcome to Pixous Technologies, {{ClientName}}!",
                    "content": "<p>Hello {{ClientName}},</p><p>Welcome to Pixous Technologies. We are thrilled to have you on board! Let's get started on {{ProjectName}}.</p>"
                },
                "whatsapp": {
                    "enabled": True,
                    "subject": "",
                    "content": "Hi {{ClientName}}! 👋 Welcome to Pixous Technologies. We're excited to start working on {{ProjectName}} with you!"
                }
            },
            "allowed_attachments": ["CompanyBrochure.pdf"],
            "sections": [],
            "checklistItems": [],
            "signoffRole": "",
            "publishing": get_default_publishing(),
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        },
        {
            "id": "2",
            "name": "Sprint Planning MOM",
            "description": "Standardize your sprint planning meetings.",
            "department": "Engineering",
            "category": "Meeting Minutes",
            "tags": ["sprint", "agile", "planning"],
            "status": "Published",
            "owner": "Scrum Master",
            "created_by": "Scrum Master",
            "updated_by": "Scrum Master",
            "version": 1,
            "language": "English",
            "visibility": "Internal",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": False,
                "footerEnabled": True,
                "letterheadEnabled": False,
                "companyDetailsEnabled": False
            },
            "channels": {},
            "allowed_attachments": [],
            "sections": get_default_sections(),
            "checklistItems": [],
            "signoffRole": "",
            "publishing": get_default_publishing(),
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        }
    ]

    checklists = [
        {
            "name": "QA Checklist",
            "description": "Pre-release quality assurance checklist for feature sign-off.",
            "items": [
                {"id": "qa1", "title": "Execute Regression Test Suite", "description": "Run the full automated regression suite and confirm no failures.", "mandatory": True, "ownerRole": "QA", "evidenceRequired": True},
                {"id": "qa2", "title": "Verify Acceptance Criteria", "description": "Confirm each acceptance criterion from the ticket has been tested and passes.", "mandatory": True, "ownerRole": "QA", "evidenceRequired": False},
                {"id": "qa3", "title": "Cross-Browser / Device Check", "description": "Validate the feature on supported browsers and device sizes.", "mandatory": False, "ownerRole": "QA", "evidenceRequired": False},
                {"id": "qa4", "title": "Log Known Issues", "description": "Document any non-blocking bugs found, with severity and ticket links.", "mandatory": False, "ownerRole": "QA", "evidenceRequired": False},
                {"id": "qa5", "title": "Sign Off for Release", "description": "QA lead confirms the build is ready to proceed to release.", "mandatory": True, "ownerRole": "Manager", "evidenceRequired": False},
            ],
        },
        {
            "name": "Deployment Checklist",
            "description": "Standardized pre- and post-deployment checklist for production releases.",
            "items": get_default_checklist_items(),
        },
    ]
    for i, cl in enumerate(checklists, start=100):
        templates.append({
            "id": str(i),
            "name": cl["name"],
            "description": cl["description"],
            "department": "Engineering",
            "category": "Checklists",
            "tags": ["checklist"],
            "status": "Published",
            "owner": "Admin",
            "created_by": "Admin",
            "updated_by": "Admin",
            "version": 1,
            "language": "English",
            "visibility": "Internal",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": False,
                "footerEnabled": False,
                "letterheadEnabled": False,
                "companyDetailsEnabled": False
            },
            "channels": {},
            "allowed_attachments": [],
            "sections": [],
            "checklistItems": cl["items"],
            "signoffRole": "Manager",
            "publishing": get_default_publishing(),
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        })

    hr_templates = [
        {
            "name": "Company Announcement", "category": "Announcements",
            "description": "General-purpose template for company-wide news and updates.",
            "email": "<p>Dear Team,</p><p>We'd like to share an important update with everyone at Pixous Technologies.</p><p><em>[Replace this paragraph with the details of your announcement.]</em></p><p>If you have any questions, please reach out to your manager or the HR team.</p><p>Thank you,<br>HR Team</p>",
            "teams": "📢 **Company Announcement**\n\nWe have an update to share with the team. *(Replace this line with the announcement details.)* Reach out to HR with any questions.",
        },
        {
            "name": "Holiday Notice (Diwali)", "category": "Announcements",
            "description": "Office closure notice for the Diwali holiday.",
            "email": "<p>Dear Team,</p><p>In celebration of Diwali, our offices will remain closed from <strong>[Start Date]</strong> to <strong>[End Date]</strong>. Regular working hours will resume on <strong>[Resume Date]</strong>.</p><p>We wish you and your family a joyous and prosperous Diwali!</p><p>Warm regards,<br>HR Team</p>",
            "teams": "🪔 **Holiday Notice — Diwali**\n\nOur offices will be closed from **[Start Date]** to **[End Date]**. We resume normal hours on **[Resume Date]**. Wishing everyone a very Happy Diwali! 🎉",
        },
        {
            "name": "Office Maintenance", "category": "Announcements",
            "description": "Notice for scheduled facility or building maintenance work.",
            "email": "<p>Dear Team,</p><p>Please be informed that scheduled maintenance work will take place at the office on <strong>[Date]</strong> between <strong>[Start Time]</strong> and <strong>[End Time]</strong>.</p><p>During this window, you may experience temporary disruption to <strong>[affected area/utility, e.g. air conditioning, elevators, Wi-Fi]</strong>. We appreciate your patience.</p><p>For urgent concerns during the maintenance window, please contact Facilities at <strong>[Contact Info]</strong>.</p><p>Regards,<br>Facilities Team</p>",
            "teams": "🛠️ **Office Maintenance Notice**\n\nScheduled maintenance on **[Date]**, **[Start Time]–[End Time]**. Expect brief disruption to **[affected area]**. Contact Facilities at **[Contact Info]** for urgent issues.",
        },
        {
            "name": "WFH Policy", "category": "Policies",
            "description": "Guidelines and expectations for employees working from home.",
            "email": "<p>Dear Team,</p><p>This notice outlines our Work-From-Home (WFH) policy:</p><ul><li><strong>Eligibility:</strong> Applicable to roles approved by your reporting manager.</li><li><strong>Availability:</strong> Be reachable during standard working hours (<strong>[e.g. 9:30 AM – 6:30 PM]</strong>) via email, chat, and calls.</li><li><strong>Equipment:</strong> Ensure a stable internet connection and a secure, company-approved device.</li><li><strong>Meetings:</strong> Keep your camera on for scheduled team meetings unless stated otherwise.</li><li><strong>Approval:</strong> Inform your manager in advance if working from a location other than your registered address.</li></ul><p>Please acknowledge that you have read and understood this policy.</p><p>Regards,<br>HR Team</p>",
            "teams": "🏠 **WFH Policy Update**\n\nKey points: be reachable during working hours, use a secure company-approved device, camera on for team meetings, and inform your manager if working from a different location. Please review and acknowledge.",
        },
        {
            "name": "Leave Policy", "category": "Policies",
            "description": "Overview of leave types, entitlements, and the application process.",
            "email": "<p>Dear Team,</p><p>Here's a summary of our leave policy:</p><ul><li><strong>Leave Types:</strong> Casual Leave, Sick Leave, Earned/Privilege Leave, and Public Holidays as per the annual calendar.</li><li><strong>Application:</strong> Apply through the HR portal at least <strong>[X days]</strong> in advance for planned leave; sick leave may be applied on the day, with manager notified directly.</li><li><strong>Approval:</strong> All leave requires your reporting manager's approval before it is considered confirmed.</li><li><strong>Carry Forward:</strong> Unused Earned Leave can be carried forward up to <strong>[X days]</strong> per the current HR guidelines.</li></ul><p>Please acknowledge that you have read and understood this policy. For questions, reach out to HR.</p><p>Regards,<br>HR Team</p>",
            "teams": "📋 **Leave Policy**\n\nCovers Casual, Sick, and Earned Leave, how to apply via the HR portal, manager approval, and carry-forward rules. Please review and acknowledge — questions go to HR.",
        },
        {
            "name": "Security Policy", "category": "Policies",
            "description": "Baseline information security practices all employees must follow.",
            "email": "<p>Dear Team,</p><p>To keep our systems and data secure, please follow these practices:</p><ul><li><strong>Passwords:</strong> Use strong, unique passwords and enable multi-factor authentication wherever available.</li><li><strong>Devices:</strong> Lock your screen when away from your desk; only use company-approved devices for work data.</li><li><strong>Email:</strong> Do not click links or download attachments from unknown or unexpected senders. Report suspicious emails to the Security team immediately.</li><li><strong>Data Handling:</strong> Do not share confidential company or client information outside approved channels.</li></ul><p>Please acknowledge that you have read and understood this policy.</p><p>Regards,<br>IT Security Team</p>",
            "teams": "🔒 **Security Policy**\n\nUse strong passwords with MFA, lock your screen when away, avoid unknown links/attachments, and never share confidential data outside approved channels. Report anything suspicious to IT Security. Please acknowledge.",
        },
        {
            "name": "Annual Townhall", "category": "Events",
            "description": "Invitation and agenda for the company's annual townhall meeting.",
            "email": "<p>Dear Team,</p><p>You're invited to our Annual Townhall!</p><ul><li><strong>Date:</strong> [Date]</li><li><strong>Time:</strong> [Time]</li><li><strong>Venue:</strong> [Venue / Video Link]</li></ul><p>Agenda highlights include a year-in-review, key business updates, and an open Q&A session with leadership. We look forward to seeing you there!</p><p>Regards,<br>HR Team</p>",
            "teams": "🎤 **Annual Townhall — Save the Date!**\n\n📅 [Date]  🕐 [Time]  📍 [Venue / Video Link]\n\nYear-in-review, business updates, and live Q&A with leadership. See you there!",
        },
        {
            "name": "Festival Celebration", "category": "Events",
            "description": "Invitation to an in-office festival celebration event.",
            "email": "<p>Dear Team,</p><p>Let's celebrate together! Join us for our festival celebration:</p><ul><li><strong>Date:</strong> [Date]</li><li><strong>Time:</strong> [Time]</li><li><strong>Venue:</strong> [Venue]</li></ul><p>Expect food, music, and fun activities for everyone. Feel free to come in festive attire!</p><p>Regards,<br>HR Team</p>",
            "teams": "🎉 **Festival Celebration!**\n\n📅 [Date]  🕐 [Time]  📍 [Venue]\n\nFood, music, and fun for everyone — come dressed in your festive best!",
        },
        {
            "name": "New Hiring", "category": "Recruitment",
            "description": "Internal announcement for an open position within the company.",
            "email": "<p>Dear Team,</p><p>We're hiring for the role of <strong>[Job Title]</strong> in the <strong>[Department]</strong> team!</p><p><strong>Key Requirements:</strong> [Skills / Experience]</p><p>If you know someone who would be a great fit, please share this opening or have them apply through <strong>[Application Link/Process]</strong>.</p><p>Regards,<br>Talent Acquisition Team</p>",
            "teams": "💼 **We're Hiring: [Job Title]**\n\nTeam: [Department] · Requirements: [Skills/Experience]\n\nKnow someone great for this role? Share this or point them to [Application Link].",
        },
        {
            "name": "Internal Referral", "category": "Recruitment",
            "description": "Reminder of the employee referral program and its rewards.",
            "email": "<p>Dear Team,</p><p>Know someone great who'd be a good fit at Pixous Technologies? Refer them through our Employee Referral Program!</p><ul><li><strong>Eligible Roles:</strong> All open positions listed on the careers page.</li><li><strong>Referral Bonus:</strong> [Amount], paid after the referred candidate completes [X months] with the company.</li><li><strong>How to Refer:</strong> Submit their details via [Referral Form/Process].</li></ul><p>Thank you for helping us grow our team!</p><p>Regards,<br>Talent Acquisition Team</p>",
            "teams": "🤝 **Refer & Earn**\n\nRefer a great candidate for any open role and earn [Amount] once they complete [X months] with us. Submit referrals via [Referral Form].",
        },
    ]
    for i, hr in enumerate(hr_templates, start=200):
        pub = get_default_publishing()
        if hr["name"] == "Company Announcement" or hr["name"] == "Holiday Notice (Diwali)":
            pub["priority"] = "High"
        if "Policy" in hr["name"]:
            pub["notificationBehavior"]["requireAcknowledgement"] = True

        templates.append({
            "id": str(i),
            "name": hr["name"],
            "description": hr["description"],
            "department": "HR",
            "category": hr["category"],
            "tags": ["hr"],
            "status": "Published",
            "owner": "HR Admin",
            "created_by": "HR Admin",
            "updated_by": "HR Admin",
            "version": 1,
            "language": "English",
            "visibility": "Internal",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": True,
                "footerEnabled": True,
                "letterheadEnabled": False,
                "companyDetailsEnabled": False
            },
            "channels": {
                "email": {
                    "enabled": True,
                    "subject": hr["name"],
                    "content": hr["email"]
                },
                "teams": {
                    "enabled": True,
                    "subject": "",
                    "content": hr["teams"]
                }
            },
            "allowed_attachments": [],
            "sections": [],
            "checklistItems": [],
            "signoffRole": "",
            "publishing": pub,
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        })

    employee_event_templates = [
        {"name": "Birthday", "eventType": "Birthday", "leadTimeDays": 0, "autoPublish": True,
         "content": "<p>🎂 Join us in wishing <strong>{{Employee}}</strong> from {{Department}} a very Happy Birthday!</p><p>\"{{Quote}}\"</p>"},
        {"name": "Anniversary", "eventType": "Anniversary", "leadTimeDays": 1, "autoPublish": True,
         "content": "<p>🎉 Congratulations to <strong>{{Employee}}</strong> on completing {{Years}} years with us in {{Department}}!</p><p>\"{{Quote}}\"</p>"},
        {"name": "Promotion", "eventType": "Promotion", "leadTimeDays": 0, "autoPublish": False,
         "content": "<p>🚀 Please join us in congratulating <strong>{{Employee}}</strong> on their well-deserved promotion in {{Department}}, under the guidance of {{Manager}}.</p>"},
        {"name": "New Joiner", "eventType": "New Joiner", "leadTimeDays": 0, "autoPublish": False,
         "content": "<p>👋 Please welcome <strong>{{Employee}}</strong> who has joined {{Department}}, reporting to {{Manager}}.</p>"},
        {"name": "Farewell", "eventType": "Farewell", "leadTimeDays": 2, "autoPublish": False,
         "content": "<p>👋 It's time to bid farewell to <strong>{{Employee}}</strong> from {{Department}} after {{Years}} years with us. We wish them the very best!</p>"},
        {"name": "Certification", "eventType": "Certification", "leadTimeDays": 0, "autoPublish": True,
         "content": "<p>🎓 Congratulations to <strong>{{Employee}}</strong> from {{Department}} on achieving a new certification!</p>"},
        {"name": "Award", "eventType": "Award", "leadTimeDays": 0, "autoPublish": False,
         "content": "<p>🏆 Congratulations to <strong>{{Employee}}</strong> from {{Department}} on receiving this month's award, recognized by {{Manager}}.</p>"},
        {"name": "Wedding", "eventType": "Wedding", "leadTimeDays": 3, "autoPublish": False,
         "content": "<p>💍 Please join us in congratulating <strong>{{Employee}}</strong> from {{Department}} on their wedding!</p>"},
        {"name": "Baby", "eventType": "Baby", "leadTimeDays": 0, "autoPublish": False,
         "content": "<p>👶 Congratulations to <strong>{{Employee}}</strong> from {{Department}} on the newest addition to their family!</p>"},
        {"name": "Achievement", "eventType": "Achievement", "leadTimeDays": 0, "autoPublish": True,
         "content": "<p>⭐ Celebrating <strong>{{Employee}}</strong> from {{Department}} for their outstanding achievement.</p><p>\"{{Quote}}\"</p>"},
    ]
    for i, ev in enumerate(employee_event_templates, start=300):
        pub = get_default_publishing()
        pub["notificationBehavior"]["allowComments"] = True

        templates.append({
            "id": str(i),
            "name": ev["name"],
            "description": f"Auto-generated employee announcement for {ev['name']} events.",
            "department": "HR",
            "category": "Employee Announcements",
            "tags": ["employee-announcement", "event-driven"],
            "status": "Published",
            "owner": "HR Admin",
            "created_by": "HR Admin",
            "updated_by": "HR Admin",
            "version": 1,
            "language": "English",
            "visibility": "Internal",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": False,
                "footerEnabled": True,
                "letterheadEnabled": False,
                "companyDetailsEnabled": False
            },
            "channels": {
                "email": {"enabled": True, "subject": f"{ev['name']} - {{{{Employee}}}}", "content": ev["content"]},
                "teams": {"enabled": True, "subject": "", "content": ev["content"]}
            },
            "allowed_attachments": [],
            "sections": [],
            "checklistItems": [],
            "signoffRole": "",
            "publishing": pub,
            "eventTrigger": {
                "enabled": True,
                "eventType": ev["eventType"],
                "autoGenerate": True,
                "autoPublish": ev["autoPublish"],
                "leadTimeDays": ev["leadTimeDays"]
            },
            "banner": ""
        })

    # Business Documents
    business_documents = [
        {
            "name": "Invoice",
            "department": "Finance",
            "owner": "Finance Admin",
            "tags": ["invoice", "billing"],
            "subject": "Invoice {{InvoiceNumber}} from Pixous Technologies",
            "content": (
                "<p>Dear {{ClientName}},</p>"
                "<p>Please find your invoice details below.</p>"
                "<table style='width:100%;border-collapse:collapse'>"
                "<tr><td><strong>Invoice Number</strong></td><td>{{InvoiceNumber}}</td></tr>"
                "<tr><td><strong>Project</strong></td><td>{{ProjectName}}</td></tr>"
                "<tr><td><strong>Amount Due</strong></td><td>{{Amount}}</td></tr>"
                "<tr><td><strong>Due Date</strong></td><td>{{DueDate}}</td></tr>"
                "</table>"
                "<p>Thank you for your business.</p>"
            ),
        },
        {
            "name": "Business Proposal",
            "department": "Sales",
            "owner": "Sales Admin",
            "tags": ["proposal", "sales"],
            "subject": "Proposal: {{ProjectName}} for {{ClientName}}",
            "content": (
                "<p>Dear {{ClientName}},</p>"
                "<p>Thank you for the opportunity to propose a solution for {{ProjectName}}.</p>"
                "<p><strong>Scope:</strong> Outline of deliverables and milestones.</p>"
                "<p><strong>Timeline:</strong> Estimated project duration and key dates.</p>"
                "<p><strong>Investment:</strong> {{Amount}}</p>"
                "<p>We look forward to partnering with you.</p>"
            ),
        },
        {
            "name": "Non-Disclosure Agreement (NDA)",
            "department": "Legal",
            "owner": "Legal Admin",
            "tags": ["nda", "legal"],
            "subject": "Mutual NDA — {{ClientName}} & Pixous Technologies",
            "content": (
                "<p>This Non-Disclosure Agreement is entered into between Pixous Technologies and {{ClientName}}.</p>"
                "<p>Both parties agree to keep confidential information related to {{ProjectName}} private and to use "
                "it solely for the purposes of evaluating and conducting the engagement.</p>"
                "<p>This agreement remains in effect until {{DueDate}} unless renewed by mutual consent.</p>"
            ),
        },
        {
            "name": "Offer Letter",
            "department": "HR",
            "owner": "HR Admin",
            "tags": ["offer-letter", "hr"],
            "subject": "Offer of Employment — {{JobTitle}}",
            "content": (
                "<p>Dear {{CandidateName}},</p>"
                "<p>We are delighted to offer you the position of <strong>{{JobTitle}}</strong> at Pixous Technologies.</p>"
                "<p>Please confirm your acceptance by {{DueDate}}. We look forward to welcoming you to the team.</p>"
            ),
        },
        {
            "name": "Purchase Order",
            "department": "Finance",
            "owner": "Finance Admin",
            "tags": ["purchase-order", "procurement"],
            "subject": "Purchase Order {{InvoiceNumber}}",
            "content": (
                "<p>Purchase Order <strong>{{InvoiceNumber}}</strong> issued to {{ClientName}} for {{ProjectName}}.</p>"
                "<table style='width:100%;border-collapse:collapse'>"
                "<tr><td><strong>Total Amount</strong></td><td>{{Amount}}</td></tr>"
                "<tr><td><strong>Delivery Due</strong></td><td>{{DueDate}}</td></tr>"
                "</table>"
            ),
        },
    ]
    for i, bd in enumerate(business_documents, start=500):
        templates.append({
            "id": str(i),
            "name": bd["name"],
            "description": f"{bd['name']} template for {bd['department']} use.",
            "department": bd["department"],
            "category": "Business Documents",
            "tags": bd["tags"],
            "status": "Published",
            "owner": bd["owner"],
            "created_by": bd["owner"],
            "updated_by": bd["owner"],
            "version": 1,
            "language": "English",
            "visibility": "Internal",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": True,
                "footerEnabled": True,
                "letterheadEnabled": True,
                "companyDetailsEnabled": True
            },
            "channels": {
                "email": {"enabled": True, "subject": bd["subject"], "content": bd["content"]}
            },
            "allowed_attachments": [],
            "sections": [],
            "checklistItems": [],
            "signoffRole": "",
            "publishing": get_default_publishing(),
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        })

    # Additional Client Communication templates
    client_comms = [
        {
            "name": "Project Status Update",
            "tags": ["status-update", "client"],
            "subject": "{{ProjectName}} — Weekly Status Update",
            "email": "<p>Hi {{ClientName}},</p><p>Here's a quick update on {{ProjectName}} this week: progress remains on track, with upcoming milestones in focus.</p>",
            "whatsapp": "Hi {{ClientName}}! Quick update on {{ProjectName}} — we're on track this week. Details in your email inbox 📩",
        },
        {
            "name": "Meeting Follow-up",
            "tags": ["follow-up", "client"],
            "subject": "Follow-up: Our Discussion on {{ProjectName}}",
            "email": "<p>Hi {{ClientName}},</p><p>Thank you for the discussion on {{ProjectName}}. As agreed, here's a summary of the key action items and next steps.</p>",
            "whatsapp": "",
        },
        {
            "name": "Invoice Payment Reminder",
            "tags": ["reminder", "billing"],
            "subject": "Payment Reminder — Invoice {{InvoiceNumber}}",
            "email": "<p>Hi {{ClientName}},</p><p>This is a friendly reminder that Invoice {{InvoiceNumber}} for {{Amount}} is due on {{DueDate}}. Please let us know if you have any questions.</p>",
            "whatsapp": "",
        },
        {
            "name": "Project Completion & Handover",
            "tags": ["handover", "closure"],
            "subject": "{{ProjectName}} — Successfully Delivered!",
            "email": "<p>Hi {{ClientName}},</p><p>We're happy to confirm that {{ProjectName}} has been completed and handed over. Thank you for trusting us with this engagement!</p>",
            "whatsapp": "Great news {{ClientName}}! {{ProjectName}} is complete and handed over. Thank you for working with us! 🎉",
        },
    ]
    for i, cc in enumerate(client_comms, start=600):
        channels = {"email": {"enabled": True, "subject": cc["subject"], "content": cc["email"]}}
        if cc["whatsapp"]:
            channels["whatsapp"] = {"enabled": True, "subject": "", "content": cc["whatsapp"]}
        templates.append({
            "id": str(i),
            "name": cc["name"],
            "description": f"{cc['name']} template for client communication.",
            "department": "Sales",
            "category": "Client Communication",
            "tags": cc["tags"],
            "status": "Published",
            "owner": "Sales Admin",
            "created_by": "Sales Admin",
            "updated_by": "Sales Admin",
            "version": 1,
            "language": "English",
            "visibility": "Public",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": True,
                "footerEnabled": True,
                "letterheadEnabled": False,
                "companyDetailsEnabled": True
            },
            "channels": channels,
            "allowed_attachments": [],
            "sections": [],
            "checklistItems": [],
            "signoffRole": "",
            "publishing": get_default_publishing(),
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        })

    # Additional Meeting Minutes templates
    meeting_minutes = [
        {
            "name": "Client Review Meeting",
            "tags": ["client", "review"],
            "sections": [
                {"id": "m1", "name": "Attendees", "type": "PeoplePicker", "enabled": True, "order": 1, "required": True, "defaultContent": ["Name", "Role", "Organization", "Attendance"]},
                {"id": "m2", "name": "Project Status", "type": "RichText", "enabled": True, "order": 2, "required": True, "defaultContent": "<strong>Overall Status:</strong> "},
                {"id": "m3", "name": "Client Feedback", "type": "RichText", "enabled": True, "order": 3, "required": False, "defaultContent": ""},
                {"id": "m4", "name": "Open Issues", "type": "Table", "enabled": True, "order": 4, "required": False, "defaultContent": ["Issue", "Owner", "Priority", "Status"]},
                {"id": "m5", "name": "Next Steps", "type": "RichText", "enabled": True, "order": 5, "required": False, "defaultContent": ""},
            ],
        },
        {
            "name": "Board Meeting Minutes",
            "tags": ["board", "governance"],
            "sections": [
                {"id": "m1", "name": "Attendees", "type": "PeoplePicker", "enabled": True, "order": 1, "required": True, "defaultContent": ["Name", "Role", "Organization", "Attendance"]},
                {"id": "m2", "name": "Previous Minutes Review", "type": "RichText", "enabled": True, "order": 2, "required": False, "defaultContent": ""},
                {"id": "m3", "name": "Agenda Items", "type": "RichText", "enabled": True, "order": 3, "required": True, "defaultContent": "1. \n2. \n3. "},
                {"id": "m4", "name": "Resolutions", "type": "Table", "enabled": True, "order": 4, "required": False, "defaultContent": ["Resolution", "Proposed By", "Votes", "Outcome"]},
                {"id": "m5", "name": "Action Items", "type": "Table", "enabled": True, "order": 5, "required": False, "defaultContent": ["Task", "Owner", "Priority", "Due Date", "Status"]},
            ],
        },
        {
            "name": "Daily Standup Notes",
            "tags": ["standup", "agile"],
            "sections": [
                {"id": "m1", "name": "Attendees", "type": "PeoplePicker", "enabled": True, "order": 1, "required": False, "defaultContent": ["Name", "Role", "Organization", "Attendance"]},
                {"id": "m2", "name": "Yesterday's Progress", "type": "RichText", "enabled": True, "order": 2, "required": True, "defaultContent": ""},
                {"id": "m3", "name": "Today's Plan", "type": "RichText", "enabled": True, "order": 3, "required": True, "defaultContent": ""},
                {"id": "m4", "name": "Blockers", "type": "RichText", "enabled": True, "order": 4, "required": False, "defaultContent": "<i>None reported</i>"},
            ],
        },
        {
            "name": "Retrospective Meeting",
            "tags": ["retrospective", "agile"],
            "sections": [
                {"id": "m1", "name": "Attendees", "type": "PeoplePicker", "enabled": True, "order": 1, "required": False, "defaultContent": ["Name", "Role", "Organization", "Attendance"]},
                {"id": "m2", "name": "What Went Well", "type": "RichText", "enabled": True, "order": 2, "required": True, "defaultContent": ""},
                {"id": "m3", "name": "What Didn't Go Well", "type": "RichText", "enabled": True, "order": 3, "required": True, "defaultContent": ""},
                {"id": "m4", "name": "Action Items", "type": "Table", "enabled": True, "order": 4, "required": False, "defaultContent": ["Task", "Owner", "Priority", "Due Date", "Status"]},
            ],
        },
    ]
    for i, mm in enumerate(meeting_minutes, start=700):
        templates.append({
            "id": str(i),
            "name": mm["name"],
            "description": f"{mm['name']} template for structured meeting notes.",
            "department": "Engineering",
            "category": "Meeting Minutes",
            "tags": mm["tags"],
            "status": "Published",
            "owner": "Admin",
            "created_by": "Admin",
            "updated_by": "Admin",
            "version": 1,
            "language": "English",
            "visibility": "Internal",
            "branding": {
                "logoEnabled": True,
                "signatureEnabled": False,
                "footerEnabled": True,
                "letterheadEnabled": False,
                "companyDetailsEnabled": False
            },
            "channels": {},
            "allowed_attachments": [],
            "sections": mm["sections"],
            "checklistItems": [],
            "signoffRole": "",
            "publishing": get_default_publishing(),
            "eventTrigger": get_default_event_trigger(),
            "banner": ""
        })

    return templates


# Each demo role gets its own separate credentials. The login page exposes a
# role selector that auto-fills these, so the shared password no longer needs
# to be displayed anywhere.
DEMO_USERS = [
    {"email": "admin@pixoustech.com", "name": "Admin User", "role": "Admin", "password": "Admin@123"},
    {"email": "editor@pixoustech.com", "name": "HR Editor", "role": "Editor", "password": "Editor@123"},
    {"email": "employee@pixoustech.com", "name": "Sample Employee", "role": "Employee", "password": "Employee@123"},
]


def sync_demo_user_passwords(db: Session):
    """Keep the seeded demo users' passwords aligned with their role-specific
    credentials so the login page auto-fill always works (including on
    databases that were seeded before the per-role passwords existed).
    Runs every startup; only rewrites a hash when it differs. Accounts whose
    password an admin reset manually are left alone."""
    changed = False
    manually_reset = get_manual_password_resets(db)
    for u in DEMO_USERS:
        if u["email"] in manually_reset:
            continue
        user = db.query(UserRecord).filter(UserRecord.email == u["email"]).first()
        if user and not verify_password(u["password"], user.hashed_password):
            user.hashed_password = hash_password(u["password"])
            changed = True
    if changed:
        db.commit()


def extract_template_variables(payload) -> list:
    """Extract the {{Placeholder}} names used anywhere in a template payload."""
    found, seen = [], set()
    texts = [payload.get("description", "")]
    for ch in payload.get("channels", {}).values():
        if isinstance(ch, dict):
            texts.append(ch.get("subject", ""))
            texts.append(ch.get("content", ""))
    for s in payload.get("sections", []):
        dc = s.get("defaultContent") if isinstance(s, dict) else None
        if isinstance(dc, str):
            texts.append(dc)
    for ci in payload.get("checklistItems", []):
        if isinstance(ci, dict):
            texts.append(ci.get("title", ""))
            texts.append(ci.get("description", ""))
    for text in texts:
        for m in VAR_NAME_PATTERN.finditer(text or ""):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                found.append(m.group(1))
    return found


def import_library(db: Session):
    """One-time, idempotent import that:

    * inserts every template from the complete business template library that
      isn't already present (matched by name),
    * fills any gaps in the variable library so every placeholder has a
      default fill value,
    * enriches every template with the standard metadata fields,
    * extends master-data departments for categories the library uses.

    Runs once per database (tracked by a config flag), so existing
    installations pick up the new library without being re-seeded.
    """
    if db.query(ConfigRecord).filter(ConfigRecord.key == LIBRARY_IMPORT_KEY).first():
        return

    existing_names = {r.payload.get("name") for r in db.query(TemplateRecord).all()}
    for t in build_library_templates():
        if t["name"] in existing_names:
            continue
        db.add(TemplateRecord(id=t["id"], payload=t))
        existing_names.add(t["name"])

    # Enrich every template with the standard metadata fields.
    for r in db.query(TemplateRecord).all():
        p = dict(r.payload)
        changed = False
        if not p.get("purpose"):
            p["purpose"] = p.get("description", "")
            changed = True
        if not isinstance(p.get("variables"), list):
            p["variables"] = extract_template_variables(p)
            changed = True
        if not p.get("created_at"):
            p["created_at"] = SEED_TIMESTAMP
            changed = True
        if not p.get("updated_at"):
            p["updated_at"] = SEED_TIMESTAMP
            changed = True
        if "approval_required" not in p:
            p["approval_required"] = False
            changed = True
        if "approved_by" not in p:
            p["approved_by"] = ""
            changed = True
        if changed:
            r.payload = p

    # Extend master-data departments for categories the library uses.
    md = db.query(ConfigRecord).filter(ConfigRecord.key == MASTER_DATA_KEY).first()
    if md:
        lists = md.payload["lists"]
        dept_items = lists["departments"]["items"]
        existing = {d["name"] for d in dept_items}
        for name in ["Facilities", "Management", "Legal"]:
            if name not in existing:
                dept_items.append(_item(name))
                existing.add(name)
        md.payload = {
            **md.payload,
            "updatedBy": "System",
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "lists": lists,
        }

    db.add(ConfigRecord(key=LIBRARY_IMPORT_KEY, payload={"importedAt": datetime.now(timezone.utc).isoformat()}))
    db.commit()


# Legacy templates (originally seeded) used [Square Bracket] placeholders,
# which the Fill & Generate flow can't fill. This pass rewrites those into
# {{VariableName}} syntax so every template gets working fill values. It is
# idempotent: once a template's brackets are converted there is nothing left
# to replace, so it simply no-ops on subsequent startups.
LEGACY_PLACEHOLDER_MAP = [
    ("[Start Date]", "{{StartDate}}"),
    ("[End Date]", "{{EndDate}}"),
    ("[Resume Date]", "{{ResumeDate}}"),
    ("[Start Time]", "{{StartTime}}"),
    ("[End Time]", "{{EndTime}}"),
    ("[Contact Info]", "{{Contact}}"),
    ("[Venue / Video Link]", "{{Venue}}"),
    ("[Venue]", "{{Venue}}"),
    ("[Job Title]", "{{JobTitle}}"),
    ("[Department]", "{{Department}}"),
    ("[Amount]", "{{Amount}}"),
    ("[X days]", "{{Days}}"),
    ("[X months]", "{{Months}}"),
    ("[e.g. 9:30 AM \u2013 6:30 PM]", "{{WorkingHours}}"),
    ("[e.g. 9:30 AM - 6:30 PM]", "{{WorkingHours}}"),
    ("[Replace this paragraph with the details of your announcement.]", "{{Announcement}}"),
    ("[Skills / Experience]", "{{Skills}}"),
    ("[Skills/Experience]", "{{Skills}}"),
    ("[Application Link/Process]", "{{ApplicationLink}}"),
    ("[Application Link]", "{{ApplicationLink}}"),
    ("[Referral Form/Process]", "{{ReferralForm}}"),
    ("[Referral Form]", "{{ReferralForm}}"),
    ("[affected area/utility, e.g. air conditioning, elevators, Wi-Fi]", "{{AffectedArea}}"),
    ("[affected area]", "{{AffectedArea}}"),
    ("[Date]", "{{Date}}"),
    ("[Time]", "{{Time}}"),
]


def _convert_text(text: str) -> str:
    for old, new in LEGACY_PLACEHOLDER_MAP:
        text = text.replace(old, new)
    return text


def convert_legacy_placeholders(db: Session):
    """Rewrite [Placeholder] style content to {{Variable}} syntax on all
    templates (runs every startup; idempotent)."""
    for r in db.query(TemplateRecord).all():
        p = dict(r.payload)
        changed = False
        for ch in p.get("channels", {}).values():
            if not isinstance(ch, dict):
                continue
            for field in ("content", "subject"):
                val = ch.get(field)
                if isinstance(val, str) and "[" in val:
                    new_val = _convert_text(val)
                    if new_val != val:
                        ch[field] = new_val
                        changed = True
        if changed:
            p["variables"] = extract_template_variables(p)
            r.payload = p
    db.commit()


def fill_missing_variables(db: Session):
    """Add any variables from the combined library that aren't present yet.
    Runs every startup so new variables reach already-seeded databases."""
    existing_var_names = {r.payload.get("name") for r in db.query(VariableRecord).all()}
    for v in build_variables() + build_library_variables():
        if v["name"] in existing_var_names:
            continue
        db.add(VariableRecord(id=v["id"], payload=v))
        existing_var_names.add(v["name"])
    db.commit()


NOTICE_BOARD_CLEANUP_KEY = "notice-board-removed-v1"


def cleanup_notice_board_templates(db: Session):
    """One-time migration: the Notice Board feature has been removed, so delete
    the seeded demo notices (identified by their 'notice-board' tag) from any
    database that already received them. Keyed so it runs exactly once and
    only ever touches templates carrying the notice-board tag — never
    user-created content."""
    if db.query(ConfigRecord).filter(ConfigRecord.key == NOTICE_BOARD_CLEANUP_KEY).first():
        return
    deleted = 0
    for r in db.query(TemplateRecord).all():
        if "notice-board" in r.payload.get("tags", []):
            db.delete(r)
            deleted += 1
    db.add(ConfigRecord(
        key=NOTICE_BOARD_CLEANUP_KEY,
        payload={"deleted": deleted, "at": datetime.now(timezone.utc).isoformat()},
    ))
    db.commit()


def seed_if_empty(db: Session):
    if db.query(TemplateRecord).count() == 0:
        for t in build_templates():
            db.add(TemplateRecord(id=t["id"], payload=t))

    if db.query(VariableRecord).count() == 0:
        for v in build_variables():
            db.add(VariableRecord(id=v["id"], payload=v))

    if db.query(UserRecord).count() == 0:
        for u in DEMO_USERS:
            db.add(UserRecord(
                id=str(uuid.uuid4()),
                email=u["email"],
                name=u["name"],
                role=u["role"],
                hashed_password=hash_password(u["password"])
            ))

    if db.query(ConfigRecord).filter(ConfigRecord.key == MASTER_DATA_KEY).first() is None:
        db.add(ConfigRecord(key=MASTER_DATA_KEY, payload=build_master_data()))

    db.commit()

    import_library(db)
    fill_missing_variables(db)
    convert_legacy_placeholders(db)
    cleanup_notice_board_templates(db)
    sync_demo_user_passwords(db)
