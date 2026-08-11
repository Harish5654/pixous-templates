"""Complete Business Template Library.

Adds the full organization template library (17 categories, 90+ templates) on
top of the original seed templates. Every template carries the standard
metadata fields:

    Template Name / Category / Description / Purpose / Template Content /
    Variables/Placeholders / Department / Owner / Version / Status /
    Created By / Created Date / Last Updated / Approval Required / Approved By

Content is authored as compact markdown and converted to HTML for the email
channel at build time. Placeholders use {{VariableName}} syntax so they map to
the global variable library and are automatically filled by the Fill &
Generate flow (the "fill values").
"""

import re
import uuid
from datetime import datetime, timezone

SEED_TIMESTAMP = "2026-08-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Markdown -> HTML (for the email channel content)
# ---------------------------------------------------------------------------

def _inline(md: str) -> str:
    """Convert **bold** inline markup; everything else passes through."""
    out = []
    i = 0
    while i < len(md):
        if md[i:i + 2] == "**":
            j = md.find("**", i + 2)
            if j != -1:
                out.append("<strong>" + md[i + 2:j] + "</strong>")
                i = j + 2
                continue
        out.append(md[i])
        i += 1
    return "".join(out)


def _parse_table(lines, i):
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(lines[i].strip())
        i += 1
    cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
    header = cells(rows[0])
    body_start = 1
    # Skip a separator row (|---|:---|) if present
    if len(rows) > 1 and re.match(r"^[\s|:\-]+$", rows[1]):
        body_start = 2
    html = ["<table style='width:100%;border-collapse:collapse;margin:8px 0'>"]
    html.append("<tr>" + "".join(
        f"<th style='border:1px solid #d0d7de;padding:6px 10px;text-align:left;background:#f6f8fa;font-size:0.85rem'>{_inline(c)}</th>"
        for c in header) + "</tr>")
    for row in rows[body_start:]:
        html.append("<tr>" + "".join(
            f"<td style='border:1px solid #d0d7de;padding:6px 10px;font-size:0.85rem'>{_inline(c)}</td>"
            for c in cells(row)) + "</tr>")
    html.append("</table>")
    return "".join(html), i


def md_to_html(md: str) -> str:
    lines = md.strip().split("\n")
    html = []
    ul_open = False
    ol_open = False

    def close_lists():
        nonlocal ul_open, ol_open
        if ul_open:
            html.append("</ul>")
            ul_open = False
        if ol_open:
            html.append("</ol>")
            ol_open = False

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            close_lists()
            i += 1
            continue
        if stripped.startswith("|"):
            close_lists()
            t, i = _parse_table(lines, i)
            html.append(t)
            continue
        if stripped == "---":
            close_lists()
            html.append("<hr style='border:none;border-top:1px solid #d0d7de;margin:12px 0' />")
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_lists()
            level = min(len(m.group(1)), 3)
            html.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue
        m = re.match(r"^[-*]\s+\[( |x)\]\s+(.*)$", stripped)
        if m:
            if ol_open:
                close_lists()
            if not ul_open:
                html.append("<ul style='padding-left:20px;margin:8px 0'>")
                ul_open = True
            html.append(f"<li>{'☐ ' if m.group(1) == ' ' else '☑ '}{_inline(m.group(2))}</li>")
            i += 1
            continue
        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            if ol_open:
                close_lists()
            if not ul_open:
                html.append("<ul style='padding-left:20px;margin:8px 0'>")
                ul_open = True
            html.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue
        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            if ul_open:
                close_lists()
            if not ol_open:
                html.append("<ol style='padding-left:20px;margin:8px 0'>")
                ol_open = True
            html.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue
        close_lists()
        html.append(f"<p>{_inline(stripped)}</p>")
        i += 1
    close_lists()
    return "".join(html)


# ---------------------------------------------------------------------------
# Variable library — every placeholder used in the library gets a default
# "fill value" so the Sample-Filled Preview and Fill & Generate both work.
# ---------------------------------------------------------------------------

def build_variables():
    V = [
        # General
        ("CompanyName", "Company Name", "String", "General", True, "Pixous Technologies", "Organization name used across templates"),
        ("Date", "Date", "Date", "General", False, "2026-08-15", "Current or reference date"),
        ("Time", "Time", "String", "General", False, "10:00 AM", "Time of the event or meeting"),
        ("Location", "Location", "String", "General", False, "Bangalore", "Physical or online location"),
        ("StartDate", "Start Date", "Date", "General", False, "2026-08-01", "Start of a period or event"),
        ("EndDate", "End Date", "Date", "General", False, "2026-08-31", "End of a period or event"),
        ("DueDate", "Due Date", "Date", "General", False, "2026-09-15", "Deadline for a response or payment"),
        ("Deadline", "Deadline", "Date", "General", False, "2026-09-30", "Target completion deadline"),
        ("TargetDate", "Target Date", "Date", "General", False, "2026-09-30", "Planned target date"),
        ("Description", "Description", "String", "General", False, "Describe the details here.", "Short description of the subject"),
        ("Reason", "Reason", "String", "General", False, "Reason for the request.", "Why this is being raised"),
        ("ActionRequired", "Action Required", "String", "General", False, "Approve and confirm.", "The action expected from the reader"),
        ("Status", "Status", "String", "General", False, "Pending", "Current status of the item"),
        ("Priority", "Priority", "String", "General", False, "Medium", "Priority level"),
        ("Severity", "Severity", "String", "General", False, "Medium", "Severity level"),
        ("Owner", "Owner", "String", "General", False, "John Doe", "Person responsible"),
        ("Approver", "Approver", "String", "General", False, "Rahul Verma", "Person who approves"),
        ("ApprovedBy", "Approved By", "String", "General", False, "Rahul Verma", "Name of the approver"),
        ("Comments", "Comments", "String", "General", False, "No additional comments.", "Additional remarks"),
        ("Contact", "Contact", "String", "General", False, "support@pixoustech.com", "Contact person or email"),
        ("Title", "Title", "String", "General", False, "Title of the document", "Document or announcement title"),
        ("Details", "Details", "String", "General", False, "Provide the important details here.", "Main body details"),
        ("Duration", "Duration", "String", "General", False, "2 hours", "Expected duration"),
        ("Number", "Number", "Number", "General", False, "10", "A numeric value such as a count"),
        ("Rating", "Rating", "Number", "General", False, "4", "Rating on a 1-5 scale"),
        ("Outcome", "Outcome", "String", "General", False, "On Track", "Overall result or status"),
        ("Steps", "Steps", "String", "General", False, "Document each step.", "Step-by-step instructions"),
        ("Topic", "Topic", "String", "General", False, "Project status", "Subject being discussed"),
        ("Question", "Question", "String", "General", False, "Open question.", "Outstanding question"),
        ("Task", "Task", "String", "General", False, "Complete the assigned task.", "A task or action item"),
        ("Action", "Action", "String", "General", False, "Follow up with the team.", "An action to be taken"),
        ("Decision", "Decision", "String", "General", False, "Approve the proposed approach.", "A decision that was made"),
        ("Signature", "Signature", "String", "General", False, "John Doe, Pixous Technologies", "Sender's signature line"),
        # People
        ("EmployeeName", "Employee Name", "String", "Employee", True, "John Doe", "Employee's full name"),
        ("EmployeeID", "Employee ID", "String", "Employee", True, "EMP-1024", "Employee identification number"),
        ("Employee", "Employee", "String", "Employee", True, "Priya Sharma", "Employee the communication is about"),
        ("Department", "Department", "String", "Employee", True, "Engineering", "Employee's department"),
        ("Designation", "Designation", "String", "Employee", False, "Senior Executive", "Job designation or title"),
        ("Manager", "Manager", "String", "Employee", False, "Rahul Verma", "Reporting manager"),
        ("ManagerName", "Manager Name", "String", "Employee", False, "Rahul Verma", "Manager's full name"),
        ("Years", "Years", "Number", "Employee", False, "5", "Years of service or experience"),
        ("Quote", "Quote", "String", "Employee", False, "Success is the sum of small efforts, repeated day in and day out.", "Motivational or congratulatory quote"),
        ("Photo", "Photo", "Image", "Employee", False, "https://i.pravatar.cc/150?img=12", "Employee's photo"),
        # Client
        ("ClientName", "Client Name", "String", "Client", True, "ABC Pvt Ltd", "Displays client's official name"),
        ("ProjectName", "Project Name", "String", "Project", True, "Project Phoenix", "The name of the project"),
        ("Milestone", "Milestone", "String", "Project", False, "Phase 1 Delivery", "A project milestone"),
        ("Phase", "Phase", "String", "Project", False, "Phase 1", "Project phase"),
        ("Risk", "Risk", "String", "Project", False, "Schedule delay due to dependencies.", "Identified risk"),
        ("Impact", "Impact", "String", "Project", False, "Low", "Impact level or description"),
        ("Objective", "Objective", "String", "Business Documents", False, "Achieve the stated goal.", "Business objective"),
        ("Requirement", "Requirement", "String", "Business Documents", False, "Define the requirement clearly.", "A business requirement"),
        ("Solution", "Solution", "String", "Business Documents", False, "Proposed solution description.", "Proposed solution"),
        ("Benefit", "Benefit", "String", "Business Documents", False, "Improved team efficiency.", "Expected benefit"),
        ("Assumption", "Assumption", "String", "Business Documents", False, "Key assumption.", "An assumption made"),
        ("Budget", "Budget", "String", "Business Documents", False, "$10,000", "Approved or estimated budget"),
        ("Cost", "Cost", "String", "Business Documents", False, "$5,000", "Estimated cost"),
        ("Amount", "Amount", "String", "Business Documents", True, "$4,500.00", "Formatted total amount due"),
        ("InvoiceNumber", "Invoice Number", "String", "Business Documents", True, "INV-2026-0142", "Unique invoice or purchase order number"),
        ("CandidateName", "Candidate Name", "String", "Business Documents", True, "Aditi Rao", "Name of the job candidate"),
        ("JobTitle", "Job Title", "String", "Business Documents", True, "Senior Software Engineer", "Job title being offered or referenced"),
        ("Position", "Position", "String", "Recruitment", True, "Senior Software Engineer", "Open position title"),
        # Announcements / Policies
        ("Announcement", "Announcement", "String", "Announcements", False, "The update to be announced.", "Announcement body text"),
        ("HolidayName", "Holiday Name", "String", "Announcements", False, "Diwali", "Holiday being observed"),
        ("PolicyName", "Policy Name", "String", "Policies", True, "Employee Code of Conduct", "Name of the policy"),
        ("PolicyNumber", "Policy Number", "String", "Policies", True, "POL-001", "Policy reference number"),
        # Meetings / Events
        ("MeetingName", "Meeting Name", "String", "Meeting Minutes", True, "Weekly Team Sync", "Name of the meeting"),
        ("Agenda", "Agenda", "String", "Meeting Minutes", False, "Review progress and next steps.", "Meeting agenda summary"),
        ("EventName", "Event Name", "String", "Events", True, "Annual Team Offsite", "Name of the event"),
        ("Venue", "Venue", "String", "Events", False, "Pixous Office, Bangalore", "Event venue"),
        ("Organizer", "Organizer", "String", "Events", False, "HR Team", "Event organizer"),
        # IT / Security / Facilities
        ("System", "System", "String", "IT", False, "Production Server", "System or device affected"),
        ("Application", "Application", "String", "IT", False, "ERP System", "Software application"),
        ("Equipment", "Equipment", "String", "IT", False, "Dell Latitude Laptop", "Hardware equipment"),
        ("Asset", "Asset", "String", "IT", False, "Laptop", "Company asset"),
        ("Condition", "Condition", "String", "IT", False, "Good", "Asset condition"),
        ("Vendor", "Vendor", "String", "Facilities", False, "Acme Services", "External vendor"),
        ("TicketID", "Ticket ID", "String", "Support", True, "SUP-2026-0042", "Support ticket number"),
        ("RequestID", "Request ID", "String", "Support", True, "REQ-2026-0107", "Request reference number"),
        ("ChangeID", "Change ID", "String", "Infrastructure", True, "INF-2026-0107", "Change request reference"),
        ("IncidentID", "Incident ID", "String", "Security", True, "SEC-2026-0107", "Incident report reference"),
        ("Resolution", "Resolution", "String", "Support", False, "Issue resolved successfully.", "How the issue was resolved"),
        ("ExpectedOutcome", "Expected Outcome", "String", "Projects", False, "Successful completion", "Expected end result"),
        ("ApprovalStatus", "Approval Status", "String", "General", False, "Approved", "Approval decision"),
        ("ResumeDate", "Resume Date", "Date", "General", False, "2026-08-18", "Date operations resume"),
        ("StartTime", "Start Time", "String", "General", False, "9:00 AM", "Start time of a window"),
        ("EndTime", "End Time", "String", "General", False, "6:00 PM", "End time of a window"),
        ("Days", "Days", "Number", "General", False, "10", "Number of days (notice, carry-forward)"),
        ("Months", "Months", "Number", "General", False, "3", "Number of months"),
        ("WorkingHours", "Working Hours", "String", "General", False, "9:30 AM – 6:30 PM", "Standard working hours"),
        ("Skills", "Skills", "String", "Recruitment", False, "Communication, teamwork, and relevant technical skills", "Skills or experience required"),
        ("ApplicationLink", "Application Link", "String", "Recruitment", False, "the careers page", "Where to apply"),
        ("ReferralForm", "Referral Form", "String", "Recruitment", False, "the referral form", "Referral submission method"),
        ("AffectedArea", "Affected Area", "String", "General", False, "the affected area", "Area affected by maintenance or change"),
    ]
    return [
        {
            "id": f"v{100 + idx}",
            "name": name,
            "display_name": display,
            "type": vtype,
            "category": category,
            "required": required,
            "default_value": default,
            "description": description,
        }
        for idx, (name, display, vtype, category, required, default, description) in enumerate(V)
    ]


# ---------------------------------------------------------------------------
# Template building blocks
# ---------------------------------------------------------------------------

def _default_publishing():
    return {
        "priority": "Normal",
        "publishImmediately": True,
        "effectiveDate": "",
        "expiryDate": "",
        "audience": {"allEmployees": True, "departments": [], "locations": [], "roles": []},
        "notificationBehavior": {"requireAcknowledgement": False, "allowComments": True, "pinToNoticeBoard": False},
    }


def _default_event_trigger():
    return {
        "enabled": False,
        "eventType": "Birthday",
        "autoGenerate": False,
        "autoPublish": False,
        "leadTimeDays": 0,
    }


def _default_branding():
    return {
        "logoEnabled": True,
        "signatureEnabled": True,
        "footerEnabled": True,
        "letterheadEnabled": False,
        "companyDetailsEnabled": True,
    }


VAR_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def _extract_variables(*texts):
    found = []
    seen = set()
    for text in texts:
        if not text:
            continue
        for m in VAR_PATTERN.finditer(text):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                found.append(m.group(1))
    return found


DEFAULT_OWNERS = {
    "Client Communication": "Sales Admin",
    "Meeting Minutes": "Admin",
    "Checklists": "Admin",
    "Announcements": "HR Admin",
    "Policies": "HR Admin",
    "Events": "HR Admin",
    "Recruitment": "HR Admin",
    "Business Documents": "Finance Admin",
    "Employee Announcements": "HR Admin",
    "Security": "IT Security Admin",
    "Infrastructure": "IT Admin",
    "IT": "IT Admin",
    "HR": "HR Admin",
    "Facilities": "Facilities Admin",
    "Projects": "PMO Admin",
    "Management": "Management Admin",
    "Support": "Support Admin",
}

DEFAULT_DEPARTMENTS = {
    "Client Communication": "Sales",
    "Meeting Minutes": "Engineering",
    "Checklists": "Engineering",
    "Announcements": "HR",
    "Policies": "HR",
    "Events": "HR",
    "Recruitment": "HR",
    "Business Documents": "Finance",
    "Employee Announcements": "HR",
    "Security": "IT",
    "Infrastructure": "IT",
    "IT": "IT",
    "HR": "HR",
    "Facilities": "Facilities",
    "Projects": "Engineering",
    "Management": "Management",
    "Support": "IT",
}


def _strip_subject_line(md: str) -> str:
    """Remove a leading **Subject:** line from the body so it isn't duplicated
    by the email channel's separate subject field."""
    lines = md.strip().split("\n")
    if lines and re.match(r"^\*\*Subject:\*\*", lines[0].strip()):
        return "\n".join(lines[1:]).strip()
    return md.strip()


def _comm(name, category, description, purpose, subject, md, tags=None, department=None,
          owner=None, visibility="Internal"):
    dept = department or DEFAULT_DEPARTMENTS[category]
    owner_name = owner or DEFAULT_OWNERS[category]
    content = md_to_html(_strip_subject_line(md))
    variables = _extract_variables(subject, content, description)
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "purpose": purpose,
        "department": dept,
        "category": category,
        "tags": tags or [],
        "status": "Published",
        "owner": owner_name,
        "created_by": owner_name,
        "updated_by": owner_name,
        "version": 1,
        "language": "English",
        "visibility": visibility,
        "branding": _default_branding(),
        "channels": {"email": {"enabled": True, "subject": subject, "content": content}},
        "allowed_attachments": [],
        "sections": [],
        "checklistItems": [],
        "signoffRole": "",
        "publishing": _default_publishing(),
        "eventTrigger": _default_event_trigger(),
        "banner": "",
        "approval_required": False,
        "approved_by": "",
        "created_at": SEED_TIMESTAMP,
        "updated_at": SEED_TIMESTAMP,
        "variables": variables,
    }


def _sec(sid, name, type_, order, required, default):
    return {"id": sid, "name": name, "type": type_, "enabled": True, "order": order, "required": required, "defaultContent": default}


def _meeting(name, description, purpose, sections, tags=None, department="Engineering"):
    owner_name = DEFAULT_OWNERS["Meeting Minutes"]
    variables = []
    for s in sections:
        if isinstance(s["defaultContent"], str):
            variables += _extract_variables(s["defaultContent"])
    variables = list(dict.fromkeys(variables))
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "purpose": purpose,
        "department": department,
        "category": "Meeting Minutes",
        "tags": tags or ["meeting"],
        "status": "Published",
        "owner": owner_name,
        "created_by": owner_name,
        "updated_by": owner_name,
        "version": 1,
        "language": "English",
        "visibility": "Internal",
        "branding": {
            "logoEnabled": True,
            "signatureEnabled": False,
            "footerEnabled": True,
            "letterheadEnabled": False,
            "companyDetailsEnabled": False,
        },
        "channels": {},
        "allowed_attachments": [],
        "sections": sections,
        "checklistItems": [],
        "signoffRole": "",
        "publishing": _default_publishing(),
        "eventTrigger": _default_event_trigger(),
        "banner": "",
        "approval_required": False,
        "approved_by": "",
        "created_at": SEED_TIMESTAMP,
        "updated_at": SEED_TIMESTAMP,
        "variables": variables,
    }


def _checklist(name, description, purpose, items, signoffRole="", department="Engineering"):
    """items: list of (title, mandatory, ownerRole, description)"""
    checklist_items = [
        {
            "id": f"c{i}",
            "title": title,
            "description": description,
            "mandatory": mandatory,
            "ownerRole": owner_role,
            "evidenceRequired": False,
        }
        for i, (title, mandatory, owner_role, description) in enumerate(items, start=1)
    ]
    owner_name = DEFAULT_OWNERS["Checklists"]
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "purpose": purpose,
        "department": department,
        "category": "Checklists",
        "tags": ["checklist"],
        "status": "Published",
        "owner": owner_name,
        "created_by": owner_name,
        "updated_by": owner_name,
        "version": 1,
        "language": "English",
        "visibility": "Internal",
        "branding": {
            "logoEnabled": True,
            "signatureEnabled": False,
            "footerEnabled": False,
            "letterheadEnabled": False,
            "companyDetailsEnabled": False,
        },
        "channels": {},
        "allowed_attachments": [],
        "sections": [],
        "checklistItems": checklist_items,
        "signoffRole": signoffRole,
        "publishing": _default_publishing(),
        "eventTrigger": _default_event_trigger(),
        "banner": "",
        "approval_required": False,
        "approved_by": "",
        "created_at": SEED_TIMESTAMP,
        "updated_at": SEED_TIMESTAMP,
        "variables": [],
    }


# ---------------------------------------------------------------------------
# The library — one entry per template
# ---------------------------------------------------------------------------

def build_library_templates():
    templates = []

    # ================= 01. CLIENT COMMUNICATION =================
    templates.append(_comm(
        "Client Update Template",
        "Client Communication",
        "Regular project update sent to clients covering progress, upcoming activities, and requests.",
        "Keep clients informed of project progress, upcoming milestones, and any items needing their attention.",
        "Project Update – {{ProjectName}}",
        """**Subject:** Project Update – {{ProjectName}}

Dear {{ClientName}},

I'm writing to provide you with an update regarding **{{ProjectName}}**.

**Current Status:** {{Outcome}}

**Progress**

* Completed task / milestone
* Completed task / milestone
* Current activity

**Upcoming Activities**

* Next activity – {{Date}}
* Next milestone – {{Date}}

**Items Requiring Your Attention**

* Approval / Information / Decision required
* Required by: {{DueDate}}

Please let us know if you have any questions or require additional information.

Best regards,
{{Signature}}""",
        tags=["client", "update"],
        visibility="Public",
    ))

    templates.append(_comm(
        "Client Introduction Email",
        "Client Communication",
        "First introduction to a new client or point of contact.",
        "Introduce your team and establish the point of contact for a new engagement.",
        "Introduction – {{CompanyName}}",
        """**Subject:** Introduction – {{CompanyName}}

Dear {{ClientName}},

My name is {{EmployeeName}}, and I am {{Designation}} at {{CompanyName}}. I will be your point of contact for {{ProjectName}}.

We look forward to working with you and supporting you with {{Description}}.

Please feel free to contact me regarding any questions or requirements.

**Contact:** {{Contact}}

Best regards,
{{Signature}}""",
        tags=["introduction", "onboarding"],
        visibility="Public",
    ))

    templates.append(_comm(
        "Client Project Update",
        "Client Communication",
        "Status update on an ongoing client project.",
        "Communicate the latest project status, completed work, and next steps to the client.",
        "Project Update – {{ProjectName}}",
        """**Subject:** Project Update – {{ProjectName}}

Dear {{ClientName}},

Here is the latest update regarding **{{ProjectName}}**.

**Overall Status:** {{Outcome}}

**Completed**

* Task / Milestone
* Task / Milestone

**In Progress**

* Task
* Task

**Next Steps**

* Task – {{Date}}
* Task – {{Date}}

**Client Action Required**

{{ActionRequired}}

Please contact us if you have any questions.

Best regards,
{{Signature}}""",
        tags=["status-update", "client"],
        visibility="Public",
    ))

    templates.append(_comm(
        "Client Meeting Follow-Up",
        "Client Communication",
        "Follow-up summary after a client meeting.",
        "Summarize discussion points and agreed actions from a client meeting.",
        "Follow-Up – {{MeetingName}} – {{Date}}",
        """**Subject:** Follow-Up – {{MeetingName}} – {{Date}}

Dear {{ClientName}},

Thank you for meeting with us on {{Date}}.

**Key Discussion Points**

* {{Topic}}
* {{Topic}}
* {{Topic}}

**Agreed Actions**

| Action | Owner | Due Date |
| --- | --- | --- |
| {{Action}} | {{Owner}} | {{DueDate}} |
| {{Action}} | {{Owner}} | {{DueDate}} |

We will continue to track the agreed actions and provide updates as required.

Best regards,
{{Signature}}""",
        tags=["follow-up", "meeting"],
        visibility="Public",
    ))

    templates.append(_comm(
        "Client Delay Notification",
        "Client Communication",
        "Notification of a project delay with corrective actions.",
        "Inform the client about a delay and the plan to minimize its impact.",
        "Project Update – {{ProjectName}}",
        """**Subject:** Project Update – {{ProjectName}}

Dear {{ClientName}},

We would like to inform you that **{{ProjectName}}** is currently experiencing a delay due to {{Reason}}.

The revised expected completion date is **{{TargetDate}}**.

**Impact**

{{Impact}}

**Corrective Action**

{{Solution}}

We apologize for any inconvenience and appreciate your understanding.

Best regards,
{{Signature}}""",
        tags=["delay", "client"],
        visibility="Public",
    ))

    templates.append(_comm(
        "Client Feedback Request",
        "Client Communication",
        "Request for client feedback on a project or service.",
        "Collect client feedback to improve services and delivery quality.",
        "We Value Your Feedback",
        """**Subject:** We Value Your Feedback

Dear {{ClientName}},

Thank you for working with {{CompanyName}}.

We would appreciate your feedback regarding {{ProjectName}}.

**Overall Experience:** {{Rating}}

**Feedback**

{{Comments}}

**Areas We Could Improve**

{{Comments}}

**Additional Comments**

{{Comments}}

Thank you for helping us improve our services.

Best regards,
{{Signature}}""",
        tags=["feedback", "client"],
        visibility="Public",
    ))

    # ================= 02. MEETING MINUTES =================
    templates.append(_meeting(
        "Meeting Minutes Template",
        "Generic meeting minutes covering agenda, discussion, decisions, and action items.",
        "Capture structured minutes for any internal or client meeting.",
        [
            _sec("m1", "Attendees", "PeoplePicker", 1, True, ["Name", "Role", "Organization", "Attendance"]),
            _sec("m2", "Agenda", "RichText", 2, True, "1. \n2. \n3. "),
            _sec("m3", "Discussion Summary", "RichText", 3, False, "<strong>Key Points:</strong><br><br><strong>Questions:</strong>"),
            _sec("m4", "Decisions Made", "Table", 4, False, ["Decision", "Owner", "Date"]),
            _sec("m5", "Action Items", "Table", 5, False, ["Action Item", "Owner", "Due Date", "Status"]),
            _sec("m6", "Next Meeting", "RichText", 6, False, "**Date:**  \n**Time:**  \n**Location:**"),
        ],
        tags=["generic", "minutes"],
    ))

    templates.append(_meeting(
        "Standard Meeting Minutes",
        "Standard format for recording a regular team or departmental meeting.",
        "Record a standard meeting with attendees, agenda, decisions, and actions.",
        [
            _sec("m1", "Meeting Details", "RichText", 1, True, "**Meeting:** {{MeetingName}}\n**Date:** {{Date}}\n**Time:** {{Time}}\n**Location:** {{Location}}"),
            _sec("m2", "Attendees", "PeoplePicker", 2, True, ["Name", "Role", "Organization", "Attendance"]),
            _sec("m3", "Agenda", "RichText", 3, True, "1. \n2. \n3. "),
            _sec("m4", "Discussion", "RichText", 4, False, "<strong>Key Points:</strong>"),
            _sec("m5", "Decisions", "Table", 5, False, ["Decision", "Decision By", "Decision Date"]),
            _sec("m6", "Action Items", "Table", 6, False, ["Task", "Owner", "Deadline", "Status"]),
            _sec("m7", "Next Meeting", "RichText", 7, False, "{{Date}} / {{Time}}"),
        ],
        tags=["standard", "minutes"],
    ))

    templates.append(_meeting(
        "Project Meeting Minutes",
        "Minutes for a project status or review meeting.",
        "Track project status, issues, risks, and actions agreed during the meeting.",
        [
            _sec("m1", "Project Details", "RichText", 1, True, "**Project:** {{ProjectName}}\n**Meeting Date:** {{Date}}\n**Project Manager:** {{ManagerName}}"),
            _sec("m2", "Project Status", "RichText", 2, True, "**Overall Status:** {{Outcome}}"),
            _sec("m3", "Completed Since Last Meeting", "RichText", 3, False, ""),
            _sec("m4", "Current Issues", "RichText", 4, False, ""),
            _sec("m5", "Risks", "RichText", 5, False, ""),
            _sec("m6", "Decisions", "Table", 6, False, ["Decision", "Decision By", "Decision Date"]),
            _sec("m7", "Actions", "Table", 7, False, ["Task", "Owner", "Due Date", "Status"]),
        ],
        tags=["project", "minutes"],
    ))

    templates.append(_meeting(
        "Management Meeting Minutes",
        "Minutes for management review meetings covering performance and decisions.",
        "Record business, financial, operational, and HR updates with management decisions.",
        [
            _sec("m1", "Attendees", "PeoplePicker", 1, True, ["Name", "Role", "Organization", "Attendance"]),
            _sec("m2", "Business Performance", "RichText", 2, True, ""),
            _sec("m3", "Financial Updates", "RichText", 3, False, ""),
            _sec("m4", "Operational Updates", "RichText", 4, False, ""),
            _sec("m5", "HR Updates", "RichText", 5, False, ""),
            _sec("m6", "Risks & Issues", "RichText", 6, False, ""),
            _sec("m7", "Management Decisions", "Table", 7, False, ["Decision", "Responsible Person", "Deadline"]),
        ],
        tags=["management", "review"],
        department="Management",
    ))

    templates.append(_meeting(
        "Client Meeting Minutes",
        "Minutes for meetings with clients about an engagement.",
        "Record client requirements, agreements, open questions, and actions.",
        [
            _sec("m1", "Meeting Details", "RichText", 1, True, "**Client:** {{ClientName}}\n**Project:** {{ProjectName}}\n**Date:** {{Date}}"),
            _sec("m2", "Participants", "PeoplePicker", 2, False, ["Name", "Role", "Organization", "Attendance"]),
            _sec("m3", "Client Requirements", "RichText", 3, True, ""),
            _sec("m4", "Discussion", "RichText", 4, False, ""),
            _sec("m5", "Agreements", "RichText", 5, False, ""),
            _sec("m6", "Open Questions", "RichText", 6, False, ""),
            _sec("m7", "Actions", "Table", 7, False, ["Action", "Responsible", "Deadline", "Status"]),
        ],
        tags=["client", "minutes"],
    ))

    templates.append(_meeting(
        "Daily Stand-Up Minutes",
        "Quick stand-up notes tracking yesterday, today, and blockers per person.",
        "Capture each team member's status in a fast daily stand-up format.",
        [
            _sec("m1", "Team Stand-Up", "Table", 1, True, ["Employee", "Yesterday", "Today", "Blockers"]),
            _sec("m2", "Decisions", "RichText", 2, False, ""),
            _sec("m3", "Follow-Up", "RichText", 3, False, ""),
        ],
        tags=["standup", "agile"],
    ))

    # ================= 03. CHECKLISTS =================
    templates.append(_checklist(
        "General Task Checklist",
        "Structured checklist for any task covering preparation, execution, and final review.",
        "Guide any task through preparation, execution, and final review phases.",
        [
            ("Confirm requirements", True, "Any", "Verify that task requirements are clear"),
            ("Gather required information", True, "Any", "Collect all information needed to start"),
            ("Identify responsible persons", True, "Any", "Assign owners for each part of the task"),
            ("Confirm deadline", True, "Any", "Agree on the completion date"),
            ("Obtain necessary approvals", False, "Manager", "Get required sign-offs before starting"),
            ("Complete Task 1", False, "Any", "Execute the first work item"),
            ("Complete Task 2", False, "Any", "Execute the second work item"),
            ("Complete Task 3", False, "Any", "Execute the third work item"),
            ("Verify completed work", True, "QA", "Check that the output meets requirements"),
            ("Document results", False, "Any", "Record what was done and how"),
            ("Quality check completed", True, "QA", "Final quality review"),
            ("Required approvals obtained", False, "Manager", "All approvals collected"),
            ("Documents filed", False, "Any", "Store documents in the right location"),
            ("Stakeholders notified", False, "Any", "Inform affected people of completion"),
            ("Checklist closed", True, "Manager", "Formally close the task"),
        ],
        signoffRole="Manager",
    ))

    templates.append(_checklist(
        "New Employee Onboarding Checklist",
        "End-to-end checklist for onboarding a new employee.",
        "Ensure every step of employee onboarding is completed without gaps.",
        [
            ("Employment documents received", True, "HR", "Collect offer letter, ID proof, and contracts"),
            ("Employee record created", True, "HR", "Create the employee master record"),
            ("ID/access card issued", True, "Facilities", "Issue employee ID card"),
            ("Email account created", True, "IT", "Provision the corporate email account"),
            ("Laptop/equipment assigned", True, "IT", "Assign and configure hardware"),
            ("Software access provided", True, "IT", "Grant required software and tool access"),
            ("Workspace assigned", True, "Facilities", "Allocate desk or workspace"),
            ("Manager introduction completed", True, "Manager", "Introduce the new hire to their manager"),
            ("Company policies provided", True, "HR", "Share policies and handbooks"),
            ("Security training completed", True, "IT", "Complete security awareness training"),
            ("HR orientation completed", True, "HR", "Complete HR orientation session"),
            ("Team introduction completed", True, "Manager", "Introduce the new hire to the team"),
        ],
        signoffRole="HR",
        department="HR",
    ))

    templates.append(_checklist(
        "Employee Offboarding Checklist",
        "Checklist for a smooth and complete employee exit.",
        "Ensure all exits are handled completely, from property return to payroll.",
        [
            ("Resignation/termination documented", True, "HR", "Record the exit decision and date"),
            ("Exit interview completed", False, "HR", "Conduct and log the exit interview"),
            ("Company property returned", True, "Facilities", "Collect ID cards, keys, and assets"),
            ("Laptop returned", True, "IT", "Collect and wipe the laptop"),
            ("ID/access card returned", True, "Facilities", "Collect the access card"),
            ("Email disabled", True, "IT", "Disable the corporate email account"),
            ("System access removed", True, "IT", "Revoke all system access"),
            ("Files transferred", False, "Manager", "Transfer ownership of work files"),
            ("Final payroll processed", True, "Finance", "Process final settlement"),
            ("Benefits updated", False, "HR", "Update benefits and insurance records"),
            ("Clearance completed", True, "HR", "Complete the full clearance process"),
        ],
        signoffRole="HR",
        department="HR",
    ))

    templates.append(_checklist(
        "Office Opening Checklist",
        "Morning checklist for opening the office.",
        "Verify the office is safe, clean, and ready before employees arrive.",
        [
            ("Security systems checked", True, "Facilities", "Verify alarms and cameras are normal"),
            ("Doors/access checked", True, "Facilities", "Confirm entry doors unlock properly"),
            ("Lights checked", True, "Facilities", "All areas lit"),
            ("HVAC checked", True, "Facilities", "Temperature and ventilation working"),
            ("Network checked", True, "IT", "Wi-Fi and connectivity up"),
            ("Meeting rooms prepared", False, "Facilities", "Rooms ready for the day"),
            ("Common areas checked", False, "Facilities", "Pantry, reception, and lobbies tidy"),
            ("Cleaning completed", False, "Facilities", "Floors and work areas cleaned"),
            ("Emergency equipment checked", True, "Facilities", "Fire and safety equipment in place"),
        ],
    ))

    templates.append(_checklist(
        "Office Closing Checklist",
        "Evening checklist for securing the office.",
        "Ensure the office is secure and powered down at the end of the day.",
        [
            ("Employees have left", True, "Facilities", "Confirm no employees remain"),
            ("Doors secured", True, "Facilities", "Lock all entry doors"),
            ("Windows checked", True, "Facilities", "Windows closed and locked"),
            ("Lights switched off", True, "Facilities", "All lights off"),
            ("HVAC adjusted", False, "Facilities", "Set to energy-saving mode"),
            ("Equipment secured", True, "Facilities", "Valuables and equipment locked away"),
            ("Sensitive documents secured", True, "Facilities", "Confidential documents stored"),
            ("Security alarm activated", True, "Facilities", "Arm the alarm system"),
        ],
    ))

    # ================= 04. ANNOUNCEMENTS =================
    templates.append(_comm(
        "Company Announcement Template",
        "Announcements",
        "General template for company-wide announcements and updates.",
        "Share important updates clearly with the whole organization.",
        "Announcement – {{Title}}",
        """**ANNOUNCEMENT**

**Title:** {{Title}}
**Date:** {{Date}}

Dear Team,

We would like to inform everyone about **{{Announcement}}**.

**Details**

{{Details}}

**Effective From:** {{StartDate}}
**Applicable To:** All Employees

**Important Information**

* Point 1
* Point 2
* Point 3

Please ensure that you take the necessary action by **{{Deadline}}**.

For questions or clarification, please contact **{{Contact}}**.

Thank you for your cooperation.

**{{CompanyName}}**
{{Department}}""",
        tags=["announcement", "company"],
    ))

    templates.append(_comm(
        "General Company Announcement",
        "Announcements",
        "Short-form company-wide announcement.",
        "Quickly notify the team about an update or change.",
        "Announcement – {{Title}}",
        """**ANNOUNCEMENT**

**Title:** {{Title}}
**Date:** {{Date}}

Dear Team,

We would like to inform you about **{{Announcement}}**.

**Details**

{{Details}}

**Effective Date:** {{StartDate}}

**Required Action**

{{ActionRequired}}

For questions, please contact {{Contact}}.

Regards,
{{Manager}}""",
        tags=["announcement", "general"],
    ))

    templates.append(_comm(
        "Office Closure Announcement",
        "Announcements",
        "Notice of an office closure for a specific date.",
        "Notify employees about an office closure and resumption of operations.",
        "Office Closure – {{Date}}",
        """**Subject:** Office Closure – {{Date}}

Dear Team,

Please be informed that the office will be closed on **{{Date}}** due to {{Reason}}.

The office will resume normal operations on **{{EndDate}}**.

Please plan your work accordingly.

Regards,
{{Manager}}""",
        tags=["closure", "office"],
    ))

    templates.append(_comm(
        "System Maintenance Announcement",
        "Announcements",
        "Notice of scheduled system maintenance.",
        "Inform employees about scheduled maintenance windows and expected impact.",
        "Scheduled System Maintenance",
        """**Subject:** Scheduled System Maintenance

Dear Team,

Scheduled maintenance will be performed on **{{System}}**.

**Date:** {{Date}}
**Start Time:** {{Time}}
**Expected Duration:** {{Duration}}

**Expected Impact**

{{Impact}}

Please save your work and complete any necessary activities before the maintenance begins.

Regards,
IT Department""",
        tags=["maintenance", "it"],
    ))

    templates.append(_comm(
        "New Process Announcement",
        "Announcements",
        "Announcement of a new process or procedure.",
        "Introduce a new process, what changes, and what employees need to do.",
        "New Process – {{Title}}",
        """**Subject:** New Process – {{Title}}

Dear Team,

Effective **{{StartDate}}**, we are introducing a new process for {{Objective}}.

**What Is Changing**

{{Details}}

**What You Need to Do**

1. {{Steps}}
2. {{Steps}}
3. {{Steps}}

**Support**

Contact {{Contact}} for assistance.

Thank you for your cooperation.""",
        tags=["process", "change"],
    ))

    templates.append(_comm(
        "Holiday Announcement",
        "Announcements",
        "Announcement of an upcoming holiday.",
        "Notify the team about an upcoming holiday and office closure.",
        "{{HolidayName}} – Office Holiday",
        """**Subject:** {{HolidayName}} – Office Holiday

Dear Team,

Please be informed that {{CompanyName}} will observe **{{HolidayName}}** on {{Date}}.

Normal operations will resume on {{EndDate}}.

We wish everyone a safe and enjoyable holiday.

Regards,
{{Manager}}""",
        tags=["holiday"],
    ))

    # ================= 05. POLICIES =================
    templates.append(_comm(
        "Company Policy Template",
        "Policies",
        "Generic company policy covering purpose, scope, responsibilities, and compliance.",
        "Draft any organizational policy with a consistent, complete structure.",
        "{{PolicyName}} – Company Policy",
        """**POLICY TITLE:** {{PolicyName}}

**Policy Number:** {{PolicyNumber}}
**Version:** 1.0
**Effective Date:** {{StartDate}}
**Review Date:** {{EndDate}}
**Policy Owner:** {{Department}}
**Approved By:** {{Approver}}

**1. Purpose**

The purpose of this policy is to {{Objective}}.

**2. Scope**

This policy applies to {{Department}}.

**3. Policy Statement**

{{Details}}

**4. Responsibilities**

**Employees:** {{Description}}

**Managers:** {{Description}}

**HR/Management:** {{Description}}

**5. Procedures**

1. {{Steps}}
2. {{Steps}}
3. {{Steps}}

**6. Exceptions**

{{Comments}}

**7. Non-Compliance**

Failure to comply with this policy may result in appropriate action.

**8. Review and Revision**

This policy will be reviewed periodically and updated when necessary.

**Approved By:** __________________
**Date:** __________________""",
        tags=["policy", "company"],
    ))

    templates.append(_comm(
        "General Company Policy",
        "Policies",
        "Short-form policy covering key sections.",
        "Publish a concise policy with purpose, scope, and review.",
        "{{PolicyName}}",
        """**Policy Name:** {{PolicyName}}
**Policy ID:** {{PolicyNumber}}
**Version:** 1.0
**Effective Date:** {{StartDate}}
**Owner:** {{Department}}

**Purpose**

{{Objective}}

**Scope**

{{Description}}

**Policy Statement**

{{Details}}

**Responsibilities**

{{Description}}

**Procedure**

1. {{Steps}}
2. {{Steps}}

**Non-Compliance**

{{Comments}}

**Review**

Reviewed periodically.

**Approved By:** {{Approver}}""",
        tags=["policy", "general"],
    ))

    templates.append(_comm(
        "Remote Work Policy",
        "Policies",
        "Guidelines for employees working remotely.",
        "Set clear expectations for remote work including hours, equipment, and security.",
        "Remote Work Policy",
        """**Policy:** Remote Work

**Purpose**

To establish guidelines for employees working remotely.

**Eligibility**

{{Description}}

**Working Hours**

{{Time}} – standard working hours apply.

**Employee Responsibilities**

* Maintain availability during working hours
* Protect company information
* Maintain a suitable work environment
* Follow security requirements

**Equipment**

{{Equipment}}

**Communication**

{{Details}}

**Approval**

Remote work must be approved by {{Approver}}.""",
        tags=["policy", "remote"],
    ))

    templates.append(_comm(
        "Information Security Policy",
        "Policies",
        "Baseline information security requirements for all employees.",
        "Protect company information and systems through clear security practices.",
        "Information Security Policy",
        """**Purpose**

To protect company information and systems.

**Requirements**

Employees must:

* Use strong passwords
* Protect company devices
* Avoid unauthorized software
* Report suspicious activity
* Protect confidential information

**Access**

System access must be authorized and limited according to job responsibilities.

**Incident Reporting**

Security incidents must be reported to {{Contact}}.""",
        tags=["policy", "security"],
    ))

    templates.append(_comm(
        "Workplace Conduct Policy",
        "Policies",
        "Professional workplace behavior standards.",
        "Establish respectful, professional standards for all employees.",
        "Workplace Conduct Policy",
        """**Purpose**

To establish professional workplace standards.

Employees are expected to:

* Treat colleagues respectfully
* Follow company policies
* Maintain professional behavior
* Avoid harassment and discrimination
* Protect company property
* Follow workplace safety requirements

Violations will be handled according to company procedures.""",
        tags=["policy", "conduct"],
    ))

    # ================= 06. EVENTS =================
    templates.append(_comm(
        "Event Planning Template",
        "Events",
        "Full event plan covering schedule, requirements, budget, and post-event tasks.",
        "Plan any event end-to-end from objective to post-event wrap-up.",
        "Event Plan – {{EventName}}",
        """**Event Name:** {{EventName}}

**Event Date:** {{Date}}
**Time:** {{Time}}
**Venue:** {{Venue}}
**Organizer:** {{Organizer}}
**Expected Participants:** {{Number}}

**Event Objective**

{{Objective}}

**Event Schedule**

| Time | Activity | Responsible Person |
| --- | --- | --- |
| {{Time}} | {{Task}} | {{Owner}} |
| {{Time}} | {{Task}} | {{Owner}} |
| {{Time}} | {{Task}} | {{Owner}} |

**Requirements**

* [ ] Venue confirmed
* [ ] Invitations sent
* [ ] Catering arranged
* [ ] Equipment arranged
* [ ] Speakers confirmed
* [ ] Security arranged
* [ ] Transportation arranged
* [ ] Registration completed

**Budget**

**Estimated Budget:** {{Budget}}
**Approved Budget:** {{Budget}}

**Contacts**

**Event Coordinator:** {{Owner}}
**Emergency Contact:** {{Contact}}

**Post-Event**

* [ ] Attendance recorded
* [ ] Feedback collected
* [ ] Expenses documented
* [ ] Event report prepared""",
        tags=["event", "planning"],
    ))

    templates.append(_comm(
        "Event Invitation",
        "Events",
        "Formal invitation to an event.",
        "Invite participants to an event with date, time, and venue details.",
        "Invitation – {{EventName}}",
        """**Subject:** Invitation – {{EventName}}

Dear {{EmployeeName}},

You are cordially invited to **{{EventName}}**.

**Date:** {{Date}}
**Time:** {{Time}}
**Venue:** {{Venue}}

**Event Details**

{{Details}}

Please confirm your attendance by {{DueDate}}.

We look forward to seeing you.

Regards,
{{Organizer}}""",
        tags=["event", "invitation"],
    ))

    templates.append(_comm(
        "Event Registration Form",
        "Events",
        "Registration form for event participants.",
        "Collect participant details and special requirements for an event.",
        "Registration – {{EventName}}",
        """**Event:** {{EventName}}

**Participant Name:** {{EmployeeName}}
**Company:** {{CompanyName}}
**Designation:** {{Designation}}
**Email:** {{Contact}}
**Phone:** 98765 43210

**Attendance:** In Person / Online

**Special Requirements:** {{Comments}}

**Registration Date:** {{Date}}""",
        tags=["event", "registration"],
    ))

    templates.append(_comm(
        "Event Feedback Form",
        "Events",
        "Feedback form to evaluate an event.",
        "Gather ratings and suggestions from event attendees.",
        "Feedback – {{EventName}}",
        """**Event:** {{EventName}}

**Rate the Event**

**Overall Experience:** {{Rating}}

**Content:** {{Rating}}
**Venue:** {{Rating}}
**Organization:** {{Rating}}
**Speakers:** {{Rating}}

**What did you like?**

{{Comments}}

**What could be improved?**

{{Comments}}

**Suggestions**

{{Comments}}""",
        tags=["event", "feedback"],
    ))

    templates.append(_comm(
        "Event Post-Event Report",
        "Events",
        "Post-event report with attendance, outcomes, and lessons learned.",
        "Document event results, budget variance, and lessons for future events.",
        "Post-Event Report – {{EventName}}",
        """**Event:** {{EventName}}
**Date:** {{Date}}
**Organizer:** {{Organizer}}

**Objective**

{{Objective}}

**Attendance**

**Expected:** {{Number}}
**Actual:** {{Number}}

**Activities**

{{Details}}

**Outcomes**

{{Outcome}}

**Feedback**

{{Comments}}

**Budget**

**Budget:** {{Budget}}
**Actual Spend:** {{Cost}}

**Lessons Learned**

{{Comments}}

**Recommendations**

{{Comments}}""",
        tags=["event", "report"],
    ))

    # ================= 07. RECRUITMENT =================
    templates.append(_comm(
        "Job Requisition Template",
        "Recruitment",
        "Detailed job requisition covering responsibilities, qualifications, and process.",
        "Formally request and document a new hire with full role details.",
        "Job Requisition – {{Position}}",
        """**Position:** {{Position}}
**Department:** {{Department}}
**Location:** {{Location}}
**Employment Type:** Full-Time / Part-Time / Contract
**Reporting To:** {{ManagerName}}
**Number of Positions:** {{Number}}

**Position Summary**

{{Description}}

**Key Responsibilities**

* {{Task}}
* {{Task}}
* {{Task}}

**Required Qualifications**

* Degree / Certification
* Years of experience: {{Years}}
* Technical skills
* Other requirements

**Preferred Qualifications**

* {{Requirement}}
* {{Requirement}}

**Salary/Benefits**

**Salary Range:** {{Amount}}
**Benefits:** {{Details}}

**Recruitment Process**

1. Application Screening
2. Initial Interview
3. Technical/Functional Interview
4. Management Interview
5. Reference Check
6. Offer
7. Onboarding

**Hiring Manager:** {{ManagerName}}
**Requested Start Date:** {{TargetDate}}""",
        tags=["requisition", "hiring"],
    ))

    templates.append(_comm(
        "Job Requisition",
        "Recruitment",
        "Short job requisition form.",
        "Quickly request approval to hire for an open position.",
        "Job Requisition – {{Position}}",
        """**Position:** {{Position}}
**Department:** {{Department}}
**Location:** {{Location}}
**Employment Type:** {{Details}}
**Hiring Manager:** {{ManagerName}}

**Reason for Hiring**

{{Reason}}

**Responsibilities**

* {{Task}}
* {{Task}}

**Qualifications**

* {{Requirement}}
* {{Requirement}}

**Salary Range**

{{Amount}}

**Target Start Date**

{{TargetDate}}""",
        tags=["requisition", "hiring"],
    ))

    templates.append(_comm(
        "Job Description",
        "Recruitment",
        "Formal job description for an open role.",
        "Publish a complete job description with responsibilities and skills.",
        "Job Description – {{Position}}",
        """**Job Title:** {{Position}}
**Department:** {{Department}}
**Reports To:** {{ManagerName}}

**Position Summary**

{{Description}}

**Responsibilities**

* {{Task}}
* {{Task}}
* {{Task}}

**Required Skills**

* {{Requirement}}
* {{Requirement}}

**Qualifications**

{{Requirement}}

**Experience**

{{Years}} years

**Working Location**

{{Location}}""",
        tags=["job-description"],
    ))

    templates.append(_comm(
        "Interview Evaluation Form",
        "Recruitment",
        "Structured evaluation form for interviewers.",
        "Score candidates consistently across defined criteria.",
        "Interview Evaluation – {{CandidateName}}",
        """**Candidate:** {{CandidateName}}
**Position:** {{Position}}
**Interviewer:** {{EmployeeName}}
**Date:** {{Date}}

| Criteria | Rating | Comments |
| --- | --- | --- |
| Technical Skills | {{Rating}} | {{Comments}} |
| Communication | {{Rating}} | {{Comments}} |
| Problem Solving | {{Rating}} | {{Comments}} |
| Teamwork | {{Rating}} | {{Comments}} |
| Experience | {{Rating}} | {{Comments}} |

**Recommendation**

* [ ] Strong Hire
* [ ] Hire
* [ ] Consider
* [ ] Do Not Hire

**Comments:** {{Comments}}""",
        tags=["interview", "evaluation"],
    ))

    templates.append(_comm(
        "Candidate Rejection Email",
        "Recruitment",
        "Polite rejection email to a candidate.",
        "Close the loop with candidates who were not selected.",
        "Update on Your Application – {{Position}}",
        """**Subject:** Update on Your Application – {{Position}}

Dear {{CandidateName}},

Thank you for your interest in the **{{Position}}** role at {{CompanyName}} and for taking the time to participate in our recruitment process.

After careful consideration, we have decided to proceed with other candidates whose experience more closely matches our current requirements.

We appreciate your interest and wish you success in your job search.

Regards,
{{Manager}}""",
        tags=["candidate", "rejection"],
    ))

    templates.append(_comm(
        "Job Offer Template",
        "Recruitment",
        "Formal job offer letter.",
        "Extend an employment offer with key terms and benefits.",
        "Employment Offer – {{Position}}",
        """**Subject:** Employment Offer – {{Position}}

Dear {{CandidateName}},

We are pleased to offer you the position of **{{Position}}** at {{CompanyName}}.

**Start Date:** {{TargetDate}}
**Location:** {{Location}}
**Reporting To:** {{ManagerName}}
**Compensation:** {{Amount}}

**Key Terms**

{{Details}}

**Benefits**

{{Description}}

Please confirm your acceptance by {{DueDate}}.

We look forward to welcoming you to the team.

Regards,
{{Manager}}""",
        tags=["offer-letter"],
    ))

    # ================= 08. BUSINESS DOCUMENTS =================
    templates.append(_comm(
        "Business Proposal Template",
        "Business Documents",
        "Detailed business proposal with objectives, solution, timeline, and cost.",
        "Structure a formal proposal from executive summary to approval.",
        "Proposal: {{ProjectName}} for {{ClientName}}",
        """**PROPOSAL TITLE:** {{ProjectName}}

**Prepared For:** {{ClientName}}
**Prepared By:** {{CompanyName}}
**Date:** {{Date}}
**Version:** 1.0

**1. Executive Summary**

{{Description}}

**2. Background**

{{Details}}

**3. Objectives**

* {{Objective}}
* {{Objective}}
* {{Objective}}

**4. Proposed Solution**

{{Solution}}

**5. Scope of Work**

**Included:**

* {{Requirement}}
* {{Requirement}}

**Excluded:**

* {{Requirement}}
* {{Requirement}}

**6. Timeline**

| Phase | Start Date | End Date |
| --- | --- | --- |
| {{Phase}} | {{StartDate}} | {{EndDate}} |
| {{Phase}} | {{StartDate}} | {{EndDate}} |

**7. Cost**

**Total Estimated Cost:** {{Cost}}

**8. Assumptions**

* {{Assumption}}
* {{Assumption}}

**9. Approval**

**Prepared By:** {{EmployeeName}}
**Approved By:** {{Approver}}
**Date:** {{Date}}""",
        tags=["proposal", "sales"],
        department="Sales",
        owner="Sales Admin",
        visibility="Public",
    ))

    templates.append(_comm(
        "Business Requirements Document",
        "Business Documents",
        "BRD capturing objectives, requirements, and acceptance criteria.",
        "Document business needs and requirements for a project or system.",
        "Business Requirements – {{ProjectName}}",
        """**Project:** {{ProjectName}}
**Document Version:** 1.0

**Business Objective**

{{Objective}}

**Current Situation**

{{Details}}

**Requirements**

| ID | Requirement | Priority |
| --- | --- | --- |
| BR-001 | {{Requirement}} | High |
| BR-002 | {{Requirement}} | Medium |

**Business Rules**

{{Details}}

**Assumptions**

{{Assumption}}

**Acceptance Criteria**

{{Requirement}}

**Approval**

{{Approver}}""",
        tags=["brd", "requirements"],
    ))

    templates.append(_comm(
        "Standard Operating Procedure",
        "Business Documents",
        "SOP template with purpose, responsibilities, procedure, and quality checks.",
        "Document repeatable procedures in a standard format.",
        "SOP – {{Title}}",
        """**SOP Name:** {{Title}}
**SOP ID:** {{PolicyNumber}}
**Version:** 1.0

**Purpose**

{{Objective}}

**Scope**

{{Description}}

**Responsibilities**

{{Owner}}

**Required Resources**

{{Equipment}}

**Procedure**

1. {{Steps}}
2. {{Steps}}
3. {{Steps}}
4. {{Steps}}

**Quality Check**

{{Requirement}}

**Records**

{{Details}}

**Review Date**

{{EndDate}}""",
        tags=["sop", "procedure"],
    ))

    templates.append(_comm(
        "Business Report",
        "Business Documents",
        "Periodic business report with metrics, achievements, and recommendations.",
        "Report on period performance with metrics and next steps.",
        "Business Report – {{Title}}",
        """**Report Title:** {{Title}}
**Reporting Period:** {{StartDate}} – {{EndDate}}
**Prepared By:** {{EmployeeName}}

**Executive Summary**

{{Description}}

**Key Metrics**

| Metric | Target | Actual | Status |
| --- | --- | --- | --- |
| {{Requirement}} | {{TargetDate}} | {{Outcome}} | {{Status}} |
| {{Requirement}} | {{TargetDate}} | {{Outcome}} | {{Status}} |

**Key Achievements**

* {{Milestone}}
* {{Milestone}}

**Challenges**

* {{Risk}}
* {{Risk}}

**Recommendations**

* {{Benefit}}
* {{Benefit}}

**Next Steps**

{{ActionRequired}}""",
        tags=["report", "metrics"],
    ))

    templates.append(_comm(
        "Business Case",
        "Business Documents",
        "Business case justifying a project or investment.",
        "Present the problem, solution, benefits, cost, and recommendation.",
        "Business Case – {{ProjectName}}",
        """**Project:** {{ProjectName}}

**Problem**

{{Description}}

**Proposed Solution**

{{Solution}}

**Benefits**

* {{Benefit}}
* {{Benefit}}

**Cost**

{{Cost}}

**Risks**

{{Risk}}

**Alternatives**

{{Requirement}}

**Recommendation**

{{Decision}}

**Approval**

**Decision:** {{ApprovalStatus}}
**Approved By:** {{Approver}}""",
        tags=["business-case"],
    ))

    # ================= 09. EMPLOYEE ANNOUNCEMENTS =================
    templates.append(_comm(
        "Employee Announcement Template",
        "Employee Announcements",
        "Generic employee announcement for promotions, joins, transfers, and more.",
        "Announce any employee-related update in a consistent format.",
        "Employee Announcement – {{EmployeeName}}",
        """**Subject:** {{Title}}

Dear Team,

We are pleased to announce **{{Announcement}}**.

**Employee Details**

**Name:** {{EmployeeName}}
**Designation:** {{Designation}}
**Department:** {{Department}}
**Effective Date:** {{StartDate}}

**Announcement**

{{Details}}

Please join us in welcoming and congratulating {{EmployeeName}}.

We wish them continued success in their role.

Regards,
{{Manager}}""",
        tags=["employee-announcement"],
    ))

    templates.append(_comm(
        "New Employee Announcement",
        "Employee Announcements",
        "Welcome announcement for a new employee.",
        "Welcome a new joiner to the team and organization.",
        "Welcome {{EmployeeName}}",
        """**Subject:** Welcome {{EmployeeName}}

Dear Team,

Please join us in welcoming **{{EmployeeName}}**, who has joined us as **{{Designation}}** in the **{{Department}}** team.

{{Description}}

Please welcome {{EmployeeName}} and support them as they begin their journey with us.

Regards,
{{Manager}}""",
        tags=["employee-announcement", "new-joiner"],
    ))

    templates.append(_comm(
        "Employee Promotion Announcement",
        "Employee Announcements",
        "Announcement of an employee promotion.",
        "Celebrate and communicate an employee's promotion.",
        "Congratulations to {{EmployeeName}}",
        """**Subject:** Congratulations to {{EmployeeName}}

Dear Team,

We are pleased to announce the promotion of **{{EmployeeName}}** to **{{Designation}}**, effective {{StartDate}}.

{{Description}}

Please join us in congratulating {{EmployeeName}} and wishing them continued success.

Regards,
{{Manager}}""",
        tags=["employee-announcement", "promotion"],
    ))

    templates.append(_comm(
        "Employee Recognition Announcement",
        "Employee Announcements",
        "Announcement recognizing an employee's achievement.",
        "Recognize employees for their contributions and achievements.",
        "Employee Recognition – {{EmployeeName}}",
        """**Subject:** Employee Recognition – {{EmployeeName}}

Dear Team,

We are pleased to recognize **{{EmployeeName}}** for {{Milestone}}.

Their contribution to {{ProjectName}} has made a valuable impact.

Congratulations and thank you for your continued commitment.

Regards,
{{Manager}}""",
        tags=["employee-announcement", "recognition"],
    ))

    templates.append(_comm(
        "Employee Transfer Announcement",
        "Employee Announcements",
        "Announcement of an internal transfer.",
        "Inform the team about an employee moving to a new department.",
        "Team Update – {{EmployeeName}}",
        """**Subject:** Team Update – {{EmployeeName}}

Dear Team,

We would like to inform you that **{{EmployeeName}}** will be moving from **{{Department}}** to **{{Location}}**, effective {{StartDate}}.

We appreciate their contributions to the current team and wish them success in their new role.

Regards,
{{Manager}}""",
        tags=["employee-announcement", "transfer"],
    ))

    templates.append(_comm(
        "Employee Farewell Announcement",
        "Employee Announcements",
        "Farewell announcement for a departing employee.",
        "Announce an employee's departure and thank them for their service.",
        "Farewell to {{EmployeeName}}",
        """**Subject:** Farewell to {{EmployeeName}}

Dear Team,

After {{Years}} years with {{CompanyName}}, **{{EmployeeName}}** will be leaving the organization effective {{EndDate}}.

We sincerely thank {{EmployeeName}} for their contributions and dedication.

Please join us in wishing them every success in their future endeavors.

Regards,
{{Manager}}""",
        tags=["employee-announcement", "farewell"],
    ))

    # ================= 10. SECURITY =================
    templates.append(_comm(
        "Security Incident Report Template",
        "Security",
        "Detailed security incident report with impact, investigation, and actions.",
        "Document security incidents completely for analysis and compliance.",
        "Security Incident Report – {{IncidentID}}",
        """**Incident ID:** {{IncidentID}}
**Date:** {{Date}}
**Time:** {{Time}}
**Location/System:** {{System}}
**Reported By:** {{EmployeeName}}
**Severity:** {{Severity}}

**Incident Description**

{{Description}}

**Incident Type**

* [ ] Unauthorized Access
* [ ] Suspicious Activity
* [ ] Data Exposure
* [ ] Physical Security Incident
* [ ] Lost/Stolen Asset
* [ ] Other

**Immediate Actions Taken**

* {{Action}}
* {{Action}}

**Impact**

{{Impact}}

**Investigation**

{{Details}}

**Corrective Actions**

* {{Action}}
* {{Action}}

**Preventive Measures**

* {{Requirement}}
* {{Requirement}}

**Incident Owner:** {{Owner}}
**Status:** {{Status}}
**Resolution Date:** {{EndDate}}""",
        tags=["security", "incident"],
    ))

    templates.append(_comm(
        "Security Incident Report",
        "Security",
        "Concise security incident report.",
        "Record the essential facts of a security incident.",
        "Security Incident – {{IncidentID}}",
        """**Incident ID:** {{IncidentID}}
**Date:** {{Date}}
**Time:** {{Time}}
**Reported By:** {{EmployeeName}}
**Location/System:** {{System}}

**Incident**

{{Description}}

**Classification**

{{Severity}}

**Impact**

{{Impact}}

**Immediate Actions**

* {{Action}}
* {{Action}}

**Investigation**

{{Details}}

**Corrective Actions**

{{Action}}

**Status**

{{Status}}""",
        tags=["security", "incident"],
    ))

    templates.append(_comm(
        "Access Request",
        "Security",
        "Request for system or area access.",
        "Formally request access with justification and approvals.",
        "Access Request – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}
**System/Area:** {{System}}

**Access Required**

{{Requirement}}

**Business Justification**

{{Reason}}

**Start Date**

{{StartDate}}

**End Date**

{{EndDate}} / Not Applicable

**Approvals**

**Manager:** {{ManagerName}}
**Security/IT:** {{Approver}}""",
        tags=["security", "access"],
    ))

    templates.append(_comm(
        "Security Audit Checklist",
        "Security",
        "Checklist for performing a security audit review.",
        "Standardize security audit review steps.",
        "Security Audit Checklist – {{System}}",
        """* [ ] Access rights reviewed
* [ ] User accounts reviewed
* [ ] Password controls reviewed
* [ ] Security logs reviewed
* [ ] Physical access reviewed
* [ ] Devices reviewed
* [ ] Backup controls reviewed
* [ ] Security incidents reviewed
* [ ] Policies reviewed
* [ ] Corrective actions documented

**Auditor:** {{EmployeeName}}
**Audit Date:** {{Date}}""",
        tags=["security", "audit"],
    ))

    templates.append(_comm(
        "Security Alert",
        "Security",
        "Urgent security alert to all employees.",
        "Warn employees about a security threat and required actions.",
        "SECURITY ALERT – {{Severity}}",
        """**SECURITY ALERT**

**Date:** {{Date}}
**Severity:** {{Severity}}

**Alert**

{{Announcement}}

**Potential Impact**

{{Impact}}

**Required Action**

1. {{Action}}
2. {{Action}}

**Do Not**

* {{Requirement}}
* {{Requirement}}

For assistance, contact {{Contact}}.""",
        tags=["security", "alert"],
    ))

    templates.append(_comm(
        "Security Access Review",
        "Security",
        "Periodic review of user access levels.",
        "Review and certify user access on a system.",
        "Security Access Review – {{System}}",
        """**Review Period:** {{StartDate}} – {{EndDate}}
**System:** {{System}}
**Reviewer:** {{EmployeeName}}

| User | Access Level | Required? | Action |
| --- | --- | --- | --- |
| {{EmployeeName}} | {{Requirement}} | Yes | Keep |
| {{EmployeeName}} | {{Requirement}} | No | Remove |

**Findings**

{{Details}}

**Actions Required**

{{Action}}

**Approved By:** {{Approver}}""",
        tags=["security", "review"],
    ))

    # ================= 11. INFRASTRUCTURE =================
    templates.append(_comm(
        "Infrastructure Change Request Template",
        "Infrastructure",
        "Detailed infrastructure change request with risk and rollback plan.",
        "Request and approve infrastructure changes with full impact analysis.",
        "Infrastructure Change – {{ChangeID}}",
        """**Change Request ID:** {{ChangeID}}
**Requested By:** {{EmployeeName}}
**Department:** {{Department}}
**Requested Date:** {{Date}}

**Change Title**

{{Title}}

**Change Description**

{{Details}}

**Reason for Change**

{{Reason}}

**Affected Infrastructure**

* {{System}}
* {{Application}}
* Database
* Storage
* Cloud Environment
* Other

**Implementation Plan**

1. {{Steps}}
2. {{Steps}}
3. {{Steps}}

**Expected Downtime**

{{Duration}}

**Risk Assessment**

**Risk Level:** {{Severity}}

**Potential Risks:**

* {{Risk}}
* {{Risk}}

**Rollback Plan**

{{Solution}}

**Approval**

**Technical Owner:** {{Owner}}
**Manager:** {{Approver}}
**Approved Date:** {{Date}}

**Completion**

**Implementation Date:** {{EndDate}}
**Status:** {{Status}}
**Remarks:** {{Comments}}""",
        tags=["infrastructure", "change"],
    ))

    templates.append(_comm(
        "Infrastructure Change Request",
        "Infrastructure",
        "Short infrastructure change request form.",
        "Quickly raise an infrastructure change for approval.",
        "Change Request – {{ChangeID}}",
        """**Change ID:** {{ChangeID}}
**System:** {{System}}
**Requester:** {{EmployeeName}}

**Change**

{{Details}}

**Reason**

{{Reason}}

**Impact**

{{Impact}}

**Risk**

{{Severity}}

**Implementation Plan**

1. {{Steps}}
2. {{Steps}}
3. {{Steps}}

**Rollback Plan**

{{Solution}}

**Maintenance Window**

{{StartDate}} / {{Time}}

**Approval**

{{Approver}}""",
        tags=["infrastructure", "change"],
    ))

    templates.append(_comm(
        "Server Maintenance Checklist",
        "Infrastructure",
        "Pre/post maintenance checklist for servers.",
        "Verify all steps before and after server maintenance.",
        "Server Maintenance – {{System}}",
        """**Server:** {{System}}
**Date:** {{Date}}

* [ ] Maintenance window confirmed
* [ ] Backup verified
* [ ] System health checked
* [ ] Disk space checked
* [ ] Services checked
* [ ] Updates applied
* [ ] Logs reviewed
* [ ] Security status checked
* [ ] Applications tested
* [ ] Monitoring restored

**Engineer:** {{EmployeeName}}""",
        tags=["infrastructure", "maintenance"],
    ))

    templates.append(_comm(
        "Network Change Request",
        "Infrastructure",
        "Request for a network component change.",
        "Document network changes, downtime, and rollback steps.",
        "Network Change – {{ChangeID}}",
        """**Request ID:** {{ChangeID}}
**Network Component:** {{System}}

**Requested Change**

{{Details}}

**Business Reason**

{{Reason}}

**Affected Users/Systems**

{{Description}}

**Implementation**

{{Steps}}

**Downtime**

{{Duration}}

**Rollback**

{{Solution}}

**Approval**

{{Approver}}""",
        tags=["infrastructure", "network"],
    ))

    templates.append(_comm(
        "Infrastructure Incident Report",
        "Infrastructure",
        "Report of an infrastructure incident and its resolution.",
        "Document infrastructure incidents with root cause and prevention.",
        "Infrastructure Incident – {{IncidentID}}",
        """**Incident ID:** {{IncidentID}}
**System:** {{System}}
**Start Time:** {{Time}}
**End Time:** {{Time}}

**Incident**

{{Description}}

**Impact**

{{Impact}}

**Root Cause**

{{Reason}}

**Resolution**

{{Resolution}}

**Preventive Action**

{{Action}}

**Incident Duration**

{{Duration}}""",
        tags=["infrastructure", "incident"],
    ))

    templates.append(_comm(
        "Disaster Recovery Test Report",
        "Infrastructure",
        "Report of a disaster recovery test.",
        "Document DR test results against RTO and RPO targets.",
        "DR Test Report – {{System}}",
        """**Test Date:** {{Date}}
**System:** {{System}}
**Test Owner:** {{Owner}}

**Objective**

{{Objective}}

**Test Scenario**

{{Details}}

**Recovery Steps**

1. {{Steps}}
2. {{Steps}}

**Recovery Time**

**Target RTO:** {{Duration}}
**Actual RTO:** {{Duration}}

**Data Recovery**

**Target RPO:** {{Duration}}
**Actual RPO:** {{Duration}}

**Result**

{{Outcome}}

**Improvements**

{{Action}}""",
        tags=["infrastructure", "disaster-recovery"],
    ))

    # ================= 12. IT =================
    templates.append(_comm(
        "IT Support Request Template",
        "IT",
        "Detailed IT support request with troubleshooting and resolution.",
        "Raise and track IT issues with full context and resolution steps.",
        "IT Support – {{TicketID}}",
        """**Ticket Number:** {{TicketID}}
**Requested By:** {{EmployeeName}}
**Department:** {{Department}}
**Date:** {{Date}}
**Priority:** {{Priority}}

**Issue/Request**

{{Description}}

**Device/System**

{{Equipment}} / {{System}}

**Problem Details**

* When did the problem start? {{Time}}
* Is the issue recurring? Yes / No
* Number of users affected: {{Number}}
* Error message: {{Details}}

**Troubleshooting Already Performed**

* {{Steps}}
* {{Steps}}

**Business Impact**

{{Impact}}

**IT Action**

{{Action}}

**Resolution**

{{Resolution}}

**Assigned To:** {{Owner}}
**Resolution Date:** {{EndDate}}
**Status:** {{Status}}""",
        tags=["it", "support"],
    ))

    templates.append(_comm(
        "IT Support Ticket",
        "IT",
        "Short IT support ticket form.",
        "Raise a concise IT support ticket.",
        "IT Ticket – {{TicketID}}",
        """**Ticket:** {{TicketID}}
**Requester:** {{EmployeeName}}
**Department:** {{Department}}
**Priority:** {{Priority}}

**Issue**

{{Description}}

**Device/System**

{{Equipment}} / {{System}}

**Error**

{{Details}}

**Troubleshooting**

{{Steps}}

**Resolution**

{{Resolution}}

**Assigned To:** {{Owner}}
**Status:** {{Status}}""",
        tags=["it", "ticket"],
    ))

    templates.append(_comm(
        "Software Access Request",
        "IT",
        "Request for access to a software application.",
        "Request application access with justification and approval.",
        "Software Access – {{Application}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}
**Application:** {{Application}}

**Access Level**

User / Admin / Other

**Business Justification**

{{Reason}}

**Required From**

{{StartDate}}

**Approval**

**Manager:** {{ManagerName}}
**IT:** {{Approver}}""",
        tags=["it", "access"],
    ))

    templates.append(_comm(
        "Hardware Request",
        "IT",
        "Request for hardware equipment.",
        "Request hardware with justification and approval.",
        "Hardware Request – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}

**Requested Equipment**

* [ ] Laptop
* [ ] Desktop
* [ ] Monitor
* [ ] Keyboard/Mouse
* [ ] Mobile Device
* [ ] Other

**Business Justification**

{{Reason}}

**Required Date**

{{TargetDate}}

**Approval**

{{ManagerName}}""",
        tags=["it", "hardware"],
    ))

    templates.append(_comm(
        "IT Maintenance Notice",
        "IT",
        "Notice of scheduled IT maintenance.",
        "Inform employees about scheduled IT maintenance.",
        "IT Maintenance – {{System}}",
        """**Subject:** IT Maintenance – {{System}}

Dear Team,

IT maintenance is scheduled for:

**System:** {{System}}
**Date:** {{Date}}
**Time:** {{Time}}
**Duration:** {{Duration}}

**Expected Impact**

{{Impact}}

Please save your work before the maintenance begins.

Regards,
IT Team""",
        tags=["it", "maintenance"],
    ))

    templates.append(_comm(
        "IT Asset Handover",
        "IT",
        "Record of company assets handed to an employee.",
        "Document assets issued to an employee with condition and confirmation.",
        "Asset Handover – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}
**Date:** {{Date}}

| Asset | Asset ID | Condition |
| --- | --- | --- |
| Laptop | {{Asset}} | {{Condition}} |
| Monitor | {{Asset}} | {{Condition}} |
| Other | {{Asset}} | {{Condition}} |

**Employee Confirmation**

I confirm receipt of the above company assets.

**Employee Signature:** __________
**IT Representative:** {{Owner}}
**Date:** __________""",
        tags=["it", "assets"],
    ))

    # ================= 13. HR =================
    templates.append(_comm(
        "HR Employee Request Template",
        "HR",
        "HR request covering leave, payroll, benefits, letters, and more.",
        "Raise any HR-related employee request in one standard format.",
        "HR Request – {{EmployeeName}}",
        """**Request Type:** Leave / Payroll / Benefits / Employment Letter / Other

**Employee Name:** {{EmployeeName}}
**Employee ID:** {{EmployeeID}}
**Department:** {{Department}}
**Manager:** {{ManagerName}}
**Request Date:** {{Date}}

**Request Details**

{{Details}}

**Supporting Information**

{{Requirement}}

**Required Action**

{{ActionRequired}}

**Approval**

**Manager Approval:** {{ApprovalStatus}}
**HR Approval:** {{ApprovalStatus}}

**HR Comments**

{{Comments}}

**Processed By:** {{Owner}}
**Completion Date:** {{EndDate}}""",
        tags=["hr", "request"],
    ))

    templates.append(_comm(
        "Leave Request",
        "HR",
        "Employee leave request form.",
        "Apply for leave with dates, type, and approvals.",
        "Leave Request – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}

**Leave Type:** {{Details}}
**Start Date:** {{StartDate}}
**End Date:** {{EndDate}}
**Number of Days:** {{Number}}

**Reason**

{{Reason}}

**Manager Approval:** {{ApprovalStatus}}

**HR Status:** {{Status}}""",
        tags=["hr", "leave"],
    ))

    templates.append(_comm(
        "Employee Information Update",
        "HR",
        "Request to update employee personal information.",
        "Update employee records with new information.",
        "Information Update – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Employee ID:** {{EmployeeID}}

**Information to Update**

* [ ] Address
* [ ] Phone
* [ ] Emergency Contact
* [ ] Bank Details
* [ ] Personal Information
* [ ] Other

**New Information**

{{Details}}

**Effective Date:** {{StartDate}}

**HR Processed By:** {{Owner}}""",
        tags=["hr", "update"],
    ))

    templates.append(_comm(
        "Performance Review",
        "HR",
        "Employee performance review form.",
        "Evaluate employee performance with ratings and development goals.",
        "Performance Review – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Position:** {{Position}}
**Review Period:** {{StartDate}} – {{EndDate}}
**Manager:** {{ManagerName}}

**Key Achievements**

* {{Milestone}}
* {{Milestone}}

**Performance Areas**

| Area | Rating | Comments |
| --- | --- | --- |
| Quality | {{Rating}} | {{Comments}} |
| Productivity | {{Rating}} | {{Comments}} |
| Teamwork | {{Rating}} | {{Comments}} |
| Communication | {{Rating}} | {{Comments}} |

**Development Goals**

* {{Objective}}
* {{Objective}}

**Overall Rating**

{{Rating}}

**Manager Comments**

{{Comments}}

**Employee Comments**

{{Comments}}""",
        tags=["hr", "performance"],
    ))

    templates.append(_comm(
        "Employee Grievance Form",
        "HR",
        "Form for raising an employee grievance.",
        "Raise grievances with details, evidence, and requested resolution.",
        "Grievance – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}
**Date:** {{Date}}

**Grievance**

{{Description}}

**Date/Location of Incident**

{{Time}} / {{Location}}

**People Involved**

{{EmployeeName}}

**Supporting Information**

{{Requirement}}

**Requested Resolution**

{{Solution}}

**HR Review**

{{Comments}}

**Status:** {{Status}}""",
        tags=["hr", "grievance"],
    ))

    templates.append(_comm(
        "Exit Interview",
        "HR",
        "Exit interview questionnaire for departing employees.",
        "Collect feedback from departing employees to improve the workplace.",
        "Exit Interview – {{EmployeeName}}",
        """**Employee:** {{EmployeeName}}
**Department:** {{Department}}
**Last Working Day:** {{EndDate}}

**Reason for Leaving**

{{Reason}}

**What Did You Like?**

{{Comments}}

**What Could Be Improved?**

{{Comments}}

**Management Feedback**

{{Comments}}

**Workplace Feedback**

{{Comments}}

**Would You Recommend the Company?**

Yes / No

**Additional Comments**

{{Comments}}""",
        tags=["hr", "exit"],
    ))

    # ================= 14. FACILITIES =================
    templates.append(_comm(
        "Facilities Maintenance Request Template",
        "Facilities",
        "Detailed facilities maintenance request.",
        "Raise and track facility maintenance issues with assignment and completion.",
        "Facilities Request – {{RequestID}}",
        """**Request ID:** {{RequestID}}
**Requested By:** {{EmployeeName}}
**Department:** {{Department}}
**Location:** {{Location}}
**Date:** {{Date}}
**Priority:** {{Priority}}

**Maintenance Issue**

{{Description}}

**Category**

* [ ] Electrical
* [ ] Plumbing
* [ ] HVAC/AC
* [ ] Furniture
* [ ] Cleaning
* [ ] Building
* [ ] Safety
* [ ] Other

**Details**

{{Details}}

**Required Action**

{{ActionRequired}}

**Assigned To**

{{Owner}} / {{Vendor}}

**Target Completion**

{{TargetDate}}

**Completion**

**Completed Date:** {{EndDate}}
**Work Performed:** {{Resolution}}
**Status:** {{Status}}

**Requester Confirmation:** __________________""",
        tags=["facilities", "maintenance"],
        department="Facilities",
        owner="Facilities Admin",
    ))

    templates.append(_comm(
        "Facilities Maintenance Request",
        "Facilities",
        "Short facilities maintenance request.",
        "Quickly raise a facility issue for resolution.",
        "Facilities Request – {{RequestID}}",
        """**Request ID:** {{RequestID}}
**Location:** {{Location}}
**Requester:** {{EmployeeName}}

**Issue Category**

* [ ] Electrical
* [ ] Plumbing
* [ ] HVAC
* [ ] Furniture
* [ ] Cleaning
* [ ] Building
* [ ] Safety

**Description**

{{Description}}

**Priority**

{{Priority}}

**Required By**

{{DueDate}}

**Resolution**

{{Resolution}}

**Status:** {{Status}}""",
        tags=["facilities", "maintenance"],
        department="Facilities",
        owner="Facilities Admin",
    ))

    templates.append(_comm(
        "Office Inspection Checklist",
        "Facilities",
        "Checklist for inspecting the office.",
        "Verify office safety and operational readiness during inspections.",
        "Office Inspection – {{Location}}",
        """**Location:** {{Location}}
**Inspection Date:** {{Date}}

* [ ] Fire exits accessible
* [ ] Emergency lighting working
* [ ] Fire extinguishers available
* [ ] Electrical equipment safe
* [ ] HVAC operational
* [ ] Restrooms clean
* [ ] Common areas clean
* [ ] Furniture safe
* [ ] Lighting operational
* [ ] Security systems operational

**Issues Found**

{{Details}}

**Corrective Actions**

{{Action}}""",
        tags=["facilities", "inspection"],
        department="Facilities",
        owner="Facilities Admin",
    ))

    templates.append(_comm(
        "Cleaning Checklist",
        "Facilities",
        "Daily cleaning checklist for the office.",
        "Ensure all office areas are cleaned and supplied.",
        "Cleaning Checklist – {{Location}}",
        """**Location:** {{Location}}
**Date:** {{Date}}

* [ ] Reception cleaned
* [ ] Work areas cleaned
* [ ] Meeting rooms cleaned
* [ ] Restrooms cleaned
* [ ] Kitchen cleaned
* [ ] Floors cleaned
* [ ] Waste removed
* [ ] Supplies replenished

**Completed By:** {{EmployeeName}}""",
        tags=["facilities", "cleaning"],
        department="Facilities",
        owner="Facilities Admin",
    ))

    templates.append(_comm(
        "Facilities Vendor Request",
        "Facilities",
        "Request for external vendor services.",
        "Engage a vendor for facility services with cost and approval.",
        "Vendor Request – {{Vendor}}",
        """**Vendor:** {{Vendor}}
**Service:** {{Title}}
**Location:** {{Location}}

**Work Required**

{{Details}}

**Requested Date**

{{TargetDate}}

**Estimated Cost**

{{Cost}}

**Vendor Contact**

{{Contact}}

**Approval**

{{Approver}}

**Completion**

{{Resolution}}""",
        tags=["facilities", "vendor"],
        department="Facilities",
        owner="Facilities Admin",
    ))

    templates.append(_comm(
        "Office Relocation Checklist",
        "Facilities",
        "Checklist for relocating the office.",
        "Plan and execute an office move without missing steps.",
        "Office Relocation – {{Location}}",
        """* [ ] New location confirmed
* [ ] Lease/facility arrangements completed
* [ ] Furniture arranged
* [ ] IT/network arranged
* [ ] Access cards issued
* [ ] Security arranged
* [ ] Utilities arranged
* [ ] Employee communication sent
* [ ] Equipment moved
* [ ] Old location cleared
* [ ] New location inspected

**Move Date:** {{StartDate}}""",
        tags=["facilities", "relocation"],
        department="Facilities",
        owner="Facilities Admin",
    ))

    # ================= 15. PROJECTS =================
    templates.append(_comm(
        "Project Status Report Template",
        "Projects",
        "Detailed project status report with milestones, risks, and budget.",
        "Report project status to stakeholders with milestones, risks, and budget.",
        "Status Report – {{ProjectName}}",
        """**Project Name:** {{ProjectName}}
**Project Manager:** {{ManagerName}}
**Reporting Period:** {{StartDate}} – {{EndDate}}
**Overall Status:** {{Outcome}}

**Project Summary**

{{Description}}

**Completed This Period**

* {{Milestone}}
* {{Milestone}}

**Currently in Progress**

* {{Task}}
* {{Task}}

**Upcoming Activities**

* {{Task}} – {{Date}}
* {{Task}} – {{Date}}

**Milestones**

| Milestone | Planned Date | Status |
| --- | --- | --- |
| {{Milestone}} | {{TargetDate}} | {{Status}} |
| {{Milestone}} | {{TargetDate}} | {{Status}} |

**Risks & Issues**

| Risk/Issue | Impact | Owner | Action |
| --- | --- | --- | --- |
| {{Risk}} | {{Impact}} | {{Owner}} | {{Action}} |

**Budget**

**Approved:** {{Budget}}
**Spent:** {{Cost}}
**Remaining:** {{Budget}}

**Decisions/Support Required**

{{Decision}}

**Next Reporting Date**

{{TargetDate}}""",
        tags=["project", "status"],
    ))

    templates.append(_comm(
        "Project Charter",
        "Projects",
        "Project charter defining scope, deliverables, and success criteria.",
        "Formally authorize a project with scope, budget, and stakeholders.",
        "Project Charter – {{ProjectName}}",
        """**Project:** {{ProjectName}}
**Project Manager:** {{ManagerName}}
**Sponsor:** {{Approver}}
**Start Date:** {{StartDate}}
**Target Date:** {{TargetDate}}

**Business Objective**

{{Objective}}

**Scope**

{{Description}}

**Deliverables**

* {{Milestone}}
* {{Milestone}}

**Stakeholders**

{{ClientName}}

**Budget**

{{Budget}}

**Risks**

{{Risk}}

**Success Criteria**

{{Requirement}}

**Approval**

{{Approver}}""",
        tags=["project", "charter"],
    ))

    templates.append(_comm(
        "Project Status Report",
        "Projects",
        "Short project status report.",
        "Give stakeholders a quick project status summary.",
        "Status Report – {{ProjectName}}",
        """**Project:** {{ProjectName}}
**Reporting Period:** {{StartDate}} – {{EndDate}}

**Overall Status:** {{Outcome}}

**Completed**

* {{Task}}
* {{Task}}

**In Progress**

* {{Task}}
* {{Task}}

**Upcoming**

* {{Task}}
* {{Task}}

**Risks**

| Risk | Impact | Mitigation |
| --- | --- | --- |
| {{Risk}} | {{Impact}} | {{Action}} |

**Issues**

{{Details}}

**Budget**

**Planned:** {{Budget}}
**Actual:** {{Cost}}

**Support Required**

{{ActionRequired}}""",
        tags=["project", "status"],
    ))

    templates.append(_comm(
        "Project Risk Register",
        "Projects",
        "Register of project risks with ratings and mitigation.",
        "Track project risks, ratings, owners, and mitigations.",
        "Risk Register – {{ProjectName}}",
        """**Project:** {{ProjectName}}

| ID | Risk | Probability | Impact | Rating | Owner | Mitigation |
| --- | --- | --- | --- | --- | --- | --- |
| R001 | {{Risk}} | Medium | {{Impact}} | Medium | {{Owner}} | {{Action}} |
| R002 | {{Risk}} | Low | {{Impact}} | Low | {{Owner}} | {{Action}} |

**Review Date**

{{EndDate}}""",
        tags=["project", "risk"],
    ))

    templates.append(_comm(
        "Project Change Request",
        "Projects",
        "Request to change project scope, timeline, or budget.",
        "Document requested changes with impact analysis and approval.",
        "Change Request – {{ProjectName}}",
        """**Change ID:** {{ChangeID}}
**Project:** {{ProjectName}}
**Requested By:** {{EmployeeName}}

**Requested Change**

{{Details}}

**Reason**

{{Reason}}

**Impact on Scope**

{{Impact}}

**Impact on Timeline**

{{Impact}}

**Impact on Budget**

{{Cost}}

**Risks**

{{Risk}}

**Recommendation**

{{Decision}}

**Decision:** {{ApprovalStatus}}

**Approved By:** {{Approver}}""",
        tags=["project", "change"],
    ))

    templates.append(_comm(
        "Project Closure Report",
        "Projects",
        "Project closure report with results and lessons learned.",
        "Formally close a project with results, budget, and lessons.",
        "Closure Report – {{ProjectName}}",
        """**Project:** {{ProjectName}}
**Project Manager:** {{ManagerName}}
**Completion Date:** {{EndDate}}

**Objectives**

{{Objective}}

**Deliverables**

* {{Milestone}}
* {{Milestone}}

**Results**

{{Outcome}}

**Budget**

**Approved:** {{Budget}}
**Actual:** {{Cost}}

**Timeline**

**Planned:** {{TargetDate}}
**Actual:** {{EndDate}}

**Lessons Learned**

{{Comments}}

**Outstanding Items**

{{Requirement}}

**Final Approval**

{{Approver}}""",
        tags=["project", "closure"],
    ))

    # ================= 16. MANAGEMENT =================
    templates.append(_comm(
        "Management Decision Template",
        "Management",
        "Structured management decision with options and impact analysis.",
        "Document a management decision with options, impact, and approval.",
        "Decision – {{Title}}",
        """**Decision Title:** {{Title}}
**Date:** {{Date}}
**Decision Owner:** {{Owner}}
**Department:** {{Department}}

**Background**

{{Details}}

**Business Need**

{{Reason}}

**Options Considered**

**Option 1 – {{Requirement}}**

{{Description}}

**Option 2 – {{Requirement}}**

{{Description}}

**Option 3 – {{Requirement}}**

{{Description}}

**Recommended Option**

{{Solution}}

**Impact**

**Financial:** {{Cost}}
**Operational:** {{Impact}}
**People:** {{Impact}}
**Risk:** {{Severity}}

**Final Decision**

{{ApprovalStatus}}

**Action Items**

| Action | Owner | Deadline |
| --- | --- | --- |
| {{Action}} | {{Owner}} | {{DueDate}} |
| {{Action}} | {{Owner}} | {{DueDate}} |

**Approved By:** {{Approver}}
**Date:** {{Date}}""",
        tags=["management", "decision"],
        department="Management",
        owner="Management Admin",
    ))

    templates.append(_comm(
        "Management Decision Record",
        "Management",
        "Record of a management decision.",
        "Keep a formal record of decisions and follow-up actions.",
        "Decision Record – {{Title}}",
        """**Decision:** {{Title}}
**Date:** {{Date}}
**Owner:** {{Owner}}

**Background**

{{Details}}

**Problem**

{{Description}}

**Options**

1. {{Requirement}}
2. {{Requirement}}
3. {{Requirement}}

**Recommendation**

{{Decision}}

**Decision**

{{ApprovalStatus}}

**Actions**

| Action | Owner | Deadline |
| --- | --- | --- |
| {{Action}} | {{Owner}} | {{DueDate}} |
| {{Action}} | {{Owner}} | {{DueDate}} |""",
        tags=["management", "decision"],
        department="Management",
        owner="Management Admin",
    ))

    templates.append(_comm(
        "Management Action Tracker",
        "Management",
        "Tracker for management action items.",
        "Track management actions with priorities, owners, and status.",
        "Action Tracker – {{MeetingName}}",
        """**Meeting/Review:** {{MeetingName}}
**Date:** {{Date}}

| Action | Owner | Priority | Due Date | Status |
| --- | --- | --- | --- | --- |
| {{Action}} | {{Owner}} | High | {{DueDate}} | Open |
| {{Action}} | {{Owner}} | Medium | {{DueDate}} | In Progress |

**Escalations**

{{Details}}

**Notes**

{{Comments}}""",
        tags=["management", "tracker"],
        department="Management",
        owner="Management Admin",
    ))

    templates.append(_comm(
        "Management Review Report",
        "Management",
        "Periodic management review report.",
        "Summarize performance across business areas for management review.",
        "Management Review – {{StartDate}}",
        """**Review Period:** {{StartDate}} – {{EndDate}}

**Business Performance**

{{Outcome}}

**Financial Performance**

{{Cost}}

**Operational Performance**

{{Description}}

**Customer Performance**

{{Comments}}

**Employee/HR Performance**

{{Comments}}

**Key Risks**

{{Risk}}

**Key Decisions Required**

{{Decision}}

**Management Recommendations**

{{Action}}""",
        tags=["management", "review"],
        department="Management",
        owner="Management Admin",
    ))

    templates.append(_comm(
        "Executive Action Plan",
        "Management",
        "Action plan for an executive objective.",
        "Define executive objectives, actions, owners, and success measures.",
        "Action Plan – {{Objective}}",
        """**Objective:** {{Objective}}
**Owner:** {{Owner}}
**Date:** {{Date}}

| Action | Owner | Priority | Deadline | Status |
| --- | --- | --- | --- | --- |
| {{Action}} | {{Owner}} | High | {{DueDate}} | Open |
| {{Action}} | {{Owner}} | Medium | {{DueDate}} | In Progress |

**Expected Outcome**

{{ExpectedOutcome}}

**Success Measure**

{{Requirement}}

**Review Date**

{{EndDate}}""",
        tags=["management", "action-plan"],
        department="Management",
        owner="Management Admin",
    ))

    templates.append(_comm(
        "Department Monthly Review",
        "Management",
        "Monthly review report for a department.",
        "Review department achievements, KPIs, budget, and priorities monthly.",
        "Monthly Review – {{Department}}",
        """**Department:** {{Department}}
**Month:** {{Date}}
**Manager:** {{ManagerName}}

**1. Key Achievements**

* {{Milestone}}
* {{Milestone}}

**2. KPIs**

| KPI | Target | Actual | Status |
| --- | --- | --- | --- |
| {{Requirement}} | {{TargetDate}} | {{Outcome}} | {{Status}} |
| {{Requirement}} | {{TargetDate}} | {{Outcome}} | {{Status}} |

**3. Challenges**

* {{Risk}}
* {{Risk}}

**4. Employee/Resource Updates**

{{Comments}}

**5. Budget**

**Budget:** {{Budget}}
**Actual:** {{Cost}}

**6. Risks**

{{Risk}}

**7. Next Month Priorities**

* {{Task}}
* {{Task}}

**8. Management Support Required**

{{ActionRequired}}""",
        tags=["management", "monthly"],
        department="Management",
        owner="Management Admin",
    ))

    # ================= 17. SUPPORT =================
    templates.append(_comm(
        "Customer/Employee Support Ticket Template",
        "Support",
        "Detailed support ticket covering issue, investigation, and resolution.",
        "Raise and track support tickets with full resolution details.",
        "Support Ticket – {{TicketID}}",
        """**Ticket ID:** {{TicketID}}

**Requester:** {{EmployeeName}}
**Email/Contact:** {{Contact}}
**Department/Customer:** {{Department}} / {{ClientName}}
**Created Date:** {{Date}}
**Priority:** {{Priority}}
**Category:** {{Details}}

**Request/Issue**

{{Description}}

**Details**

{{Details}}

**Business/User Impact**

{{Impact}}

**Support Investigation**

{{Solution}}

**Actions Taken**

1. {{Action}}
2. {{Action}}
3. {{Action}}

**Resolution**

{{Resolution}}

**User Confirmation**

Confirmed / Not Confirmed

**Status**

{{Status}}

**Assigned To:** {{Owner}}
**Resolved Date:** {{EndDate}}
**Resolution Notes:** {{Comments}}""",
        tags=["support", "ticket"],
    ))

    templates.append(_comm(
        "General Support Ticket",
        "Support",
        "Short general support ticket.",
        "Raise a concise support ticket.",
        "Support Ticket – {{TicketID}}",
        """**Ticket ID:** {{TicketID}}
**Requester:** {{EmployeeName}}
**Date:** {{Date}}
**Category:** {{Details}}
**Priority:** {{Priority}}

**Request**

{{Description}}

**Impact**

{{Impact}}

**Investigation**

{{Solution}}

**Action Taken**

{{Action}}

**Resolution**

{{Resolution}}

**Status:** {{Status}}""",
        tags=["support", "ticket"],
    ))

    templates.append(_comm(
        "Customer Complaint",
        "Support",
        "Formal customer complaint record.",
        "Record customer complaints and their resolution.",
        "Complaint – {{TicketID}}",
        """**Complaint ID:** {{TicketID}}
**Customer:** {{ClientName}}
**Date:** {{Date}}

**Complaint**

{{Description}}

**Product/Service**

{{ProjectName}}

**Impact**

{{Impact}}

**Investigation**

{{Solution}}

**Corrective Action**

{{Action}}

**Customer Response**

{{Comments}}

**Resolution**

{{Resolution}}

**Status:** {{Status}}""",
        tags=["support", "complaint"],
    ))

    templates.append(_comm(
        "Service Request",
        "Support",
        "Request for a service.",
        "Raise a service request with requirements and approval.",
        "Service Request – {{RequestID}}",
        """**Request ID:** {{RequestID}}
**Requester:** {{EmployeeName}}

**Requested Service**

{{Title}}

**Business Reason**

{{Reason}}

**Required Date**

{{TargetDate}}

**Requirements**

* {{Requirement}}
* {{Requirement}}

**Approval**

{{Approver}}

**Completion**

{{Resolution}}""",
        tags=["support", "service"],
    ))

    templates.append(_comm(
        "Escalation Request",
        "Support",
        "Escalation of an unresolved ticket.",
        "Escalate an issue to the right team with context and target dates.",
        "Escalation – {{TicketID}}",
        """**Ticket ID:** {{TicketID}}
**Current Owner:** {{Owner}}
**Escalation Date:** {{Date}}

**Reason for Escalation**

{{Reason}}

**Issue Summary**

{{Description}}

**Customer/Business Impact**

{{Impact}}

**Actions Already Taken**

{{Action}}

**Escalation Required To**

{{ManagerName}}

**Expected Resolution**

{{Resolution}}

**Target Date**

{{DueDate}}""",
        tags=["support", "escalation"],
    ))

    templates.append(_comm(
        "Support Resolution Confirmation",
        "Support",
        "Confirmation that a support issue was resolved.",
        "Confirm resolution with the requester and collect feedback.",
        "Resolution Confirmation – {{TicketID}}",
        """**Ticket ID:** {{TicketID}}
**Requester:** {{EmployeeName}}
**Issue:** {{Description}}

**Resolution Provided**

{{Resolution}}

**Date Resolved**

{{EndDate}}

**Confirmation**

I confirm that the issue/request has been addressed.

**Requester:** {{EmployeeName}}
**Confirmation:** Confirmed / Not Confirmed

**Additional Feedback**

{{Comments}}""",
        tags=["support", "confirmation"],
    ))

    return templates
