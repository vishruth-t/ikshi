# ikshi — OpenCV SFace Attendance System

**Version:** 1.2  
**Status:** MVP Specification  
**Recognition:** OpenCV SFace  
**Computer Vision:** OpenCV  
**UI:** PySide6  
**Database:** SQLite  
**ML Framework:** OpenCV DNN only

> **Technology decision:** ikshi does not use Hugging Face, Transformers, PyTorch, or any Hugging Face model repository. Face recognition is implemented entirely with OpenCV SFace and the required OpenCV model files.

## Approved MVP Stack

| Area | Technology |
|---|---|
| Language | Python |
| Camera | OpenCV |
| Face detection | OpenCV DNN face detector |
| Face recognition | OpenCV SFace |
| Recognition API | `cv2.FaceRecognizerSF` |
| ML runtime | OpenCV DNN |
| Numerical processing | NumPy |
| Desktop UI | PySide6 |
| Database | SQLite |
| Export | CSV |
| Testing | pytest |

## Explicitly Excluded

The MVP must not depend on:

- Hugging Face
- Hugging Face Hub
- Transformers
- PyTorch
- `transformers`
- `torch`
- `sentence-transformers`
- Cloud-based face-recognition APIs

Model files are downloaded/provisioned separately and stored locally under `models/`.

---


## 1. Product Overview

### Product Name

**ikshi**

### One-line Description

A privacy-conscious attendance system that uses a webcam to detect and recognize registered students and automatically record their attendance.

### Problem

Manual attendance is:

- Time-consuming
- Easy to manipulate
- Difficult to maintain
- Difficult to analyze over time
- Repetitive for teachers/staff

The system automates attendance by recognizing registered students from a live camera feed.

### Core Workflow

```text
Student approaches camera
          ↓
      Webcam feed
          ↓
    OpenCV captures frame
          ↓
      Face detection
          ↓
   Face alignment/crop
          ↓
  recognition
          ↓
   Generate embedding
          ↓
 Compare with registered faces
          ↓
 ┌────────┴────────┐
 │                 │
Match            No match
 │                 │
 ↓                 ↓
Student          Unknown
identified
 │
 ↓
Check attendance
 │
 ├── Already marked → Ignore
 │
 └── Not marked → Mark Present
```

---

## 2. Goals

### Primary Goals

The system should:

1. Detect faces through a webcam.
2. Recognize registered individuals.
3. Distinguish registered people from unknown people.
4. Record attendance automatically.
5. Prevent duplicate attendance entries.
6. Store attendance in a database.
7. Allow administrators to register students.
8. Provide attendance reports.
9. Run primarily on the local machine.
10. Provide a simple user interface.

### Secondary Goals

Eventually support:

- Multiple classrooms
- Multiple cameras
- CSV/Excel export
- Monthly reports
- Attendance percentage
- Liveness detection
- Admin authentication
- Web dashboard
- Cloud synchronization

---

## 3. Non-Goals for MVP

Do not build these initially:

- Mobile application
- Cloud infrastructure
- Complex school management system
- Automatic timetable generation
- Payroll
- Advanced analytics
- Training a facial-recognition model from scratch
- Multi-camera distributed infrastructure

The first milestone is:

> **Camera → recognize student → record attendance.**

---

## 4. Target Users

### Admin

Responsible for:

- Registering students
- Removing students
- Managing student information
- Viewing attendance
- Exporting reports
- Configuring the system

### Teacher

Responsible for:

- Starting an attendance session
- Monitoring recognition
- Viewing today's attendance
- Ending a session
- Generating reports

### Student

Students do not directly operate the system.

Their interaction is:

```text
Stand in front of camera
        ↓
Face recognized
        ↓
Attendance recorded
```

---

# 5. Functional Requirements

## FR-01 — Webcam

The system must:

- Detect available cameras.
- Allow selecting a camera.
- Start/stop video capture.
- Display the live feed.
- Handle camera disconnection gracefully.

Example:

```text
Camera:
[ Integrated Webcam ▼ ]

[ Start Camera ]
[ Stop Camera ]
```

---

## FR-02 — Face Detection

The system must identify faces within each video frame.

Example output:

```text
┌─────────────────────────┐
│                         │
│    ┌──────────────┐     │
│    │              │     │
│    │     FACE     │     │
│    │              │     │
│    └──────────────┘     │
│                         │
└─────────────────────────┘
```

Detection and recognition must remain separate components.

---

## FR-03 — Face Recognition

Once a face is detected:

```text
Face
 ↓
Crop
 ↓
Preprocess
 ↓
 model
 ↓
Embedding
 ↓
Similarity comparison
 ↓
Identity
```

The preferred architecture is embedding-based recognition rather than treating an image-classification probability as identity.

```text
Registered Darshan
       ↓
Face embedding
       ↓
Stored

Camera Darshan
       ↓
Face embedding
       ↓
Compare
       ↓
Darshan
```

The exact  model should be selected through evaluation of accuracy, performance, license, model size, and suitability for local inference.

---

## FR-04 — Student Registration

Admin should be able to register a student.

### Registration Form

```text
Register Student

Student ID:
[ 2026001 ]

Name:
[ Darshan ]

Department:
[ Computer Science ]

Year:
[ 3 ]

                [Capture Face]

                [Save Student]
```

### Registration Workflow

```text
Enter student information
        ↓
Start camera
        ↓
Detect face
        ↓
Check image quality
        ↓
Capture multiple samples
        ↓
Generate embeddings
        ↓
Store embeddings
        ↓
Student registered
```

---

## FR-05 — Face Enrollment

Do not register someone using only one random frame.

Capture several samples with small variations:

```text
Sample 1 → straight
Sample 2 → slight left
Sample 3 → slight right
Sample 4 → different expression
Sample 5 → different lighting
```

The exact number should be configurable.

Prefer storing face embeddings rather than retaining raw face photographs unnecessarily.

---

## FR-06 — Recognition Threshold

The system must distinguish:

- Strong match
- Weak match
- Unknown

Example:

```text
Similarity

Darshan    0.91  ← best
Rahul      0.63
Ankit      0.51
```

If the configured threshold is `0.80`:

```text
0.91 → Darshan
0.63 → Unknown
0.51 → Unknown
```

The threshold must be validated against the selected model and actual camera/environment rather than blindly hard-coded.

---

## FR-07 — Unknown Person Handling

If no registered identity passes the recognition threshold:

```text
┌──────────────────────┐
│       UNKNOWN        │
│                      │
│   Face detected      │
│   Not recognized     │
└──────────────────────┘
```

Unknown people must not receive attendance.

---

## FR-08 — Attendance Recording

When a person is successfully recognized:

```text
Recognition
     ↓
Is identity valid?
     ↓
Is attendance already recorded today?
     │
 ┌───┴────┐
Yes      No
 │        │
Ignore   Record
```

Example record:

```text
student_id: 2026001
date:       2026-09-01
time:       09:42:15
status:     PRESENT
```

---

## FR-09 — Duplicate Prevention

A person appearing for 30 seconds could produce hundreds of recognized frames.

The database must enforce a uniqueness rule such as:

```text
(student_id, attendance_date)
```

or, for session-based attendance:

```text
(session_id, student_id)
```

This prevents duplicate attendance records.

---

## FR-10 — Recognition Stability

Do not mark someone present from a single frame.

Use temporal confirmation:

```text
Frame 1 → Darshan
Frame 2 → Darshan
Frame 3 → Darshan
Frame 4 → Darshan
        ↓
Confirmed
        ↓
Attendance
```

The number of required confirmations should be configurable.

---

## FR-11 — Attendance Session

A teacher should be able to start an attendance session.

```text
Today's Class

Date: 01 September 2026
Subject: Computer Vision
Class: CSE-A

[ START ATTENDANCE ]
```

During the session:

```text
Attendance Running

Recognized: 18
Present:    18
Remaining:  12

[ STOP ]
```

---

## FR-12 — Live Attendance Dashboard

Example:

```text
┌─────────────────────────────────────────┐
│              ATTENDANCE                 │
├────────────────────┬────────────────────┤
│                    │                    │
│                    │ Present: 18        │
│     CAMERA         │ Absent: 12         │
│                    │ Unknown: 2         │
│    [Darshan]       │                    │
│                    │ ─────────────────  │
│                    │ Darshan ✓          │
│                    │ Rahul ✓            │
│                    │ Ankit ✓            │
│                    │ Priya ✓            │
│                    │                    │
└────────────────────┴────────────────────┘
```

---

## FR-13 — Student Management

Admin should be able to:

- Add student
- View student
- Edit student
- Delete/deactivate student
- Re-enroll face
- Enable/disable student

Example:

```text
Students

ID       Name       Department       Status
------------------------------------------------
1001     Darshan    CSE              Active
1002     Rahul      CSE              Active
1003     Ankit      ECE              Active
```

---

## FR-14 — Attendance Reports

Users should be able to select:

```text
Date:
[ 01/09/2026 ]

Class:
[ CSE-A ]

[ Generate Report ]
```

Output:

```text
Student       Status       Time
-----------------------------------
Darshan       Present      09:42
Rahul         Present      09:43
Ankit         Absent       --
Priya         Present      09:45
```

---

## FR-15 — Export

MVP should support:

- CSV

Later:

- Excel
- PDF

Example CSV:

```csv
student_id,name,date,time,status
1001,Darshan,2026-09-01,09:42,PRESENT
1002,Rahul,2026-09-01,09:43,PRESENT
```

---

# 6. Database Design

Use SQLite for the initial version.

## `students`

```text
students
-----------------------------
id
student_number
name
department
year
active
created_at
updated_at
```

## `face_embeddings`

```text
face_embeddings
-----------------------------
id
student_id
embedding
model_name
created_at
```

A student may have multiple embeddings.

## `attendance_sessions`

```text
attendance_sessions
-----------------------------
id
date
subject
class_name
started_at
ended_at
```

## `attendance`

```text
attendance
-----------------------------
id
session_id
student_id
marked_at
status
confidence
```

---

# 7. System Architecture

```text
                    APPLICATION
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
      UI Layer      Recognition Layer   Database
        │                │                 │
        ▼                ▼                 ▼
    Tkinter          OpenCV            SQLite
                         │
                         ▼
                  Face Detection
                         │
                         ▼
                  Face Alignment
                         │
                         ▼
                 Model
                         │
                         ▼
                    Embedding
                         │
                         ▼
                 Similarity Engine
```

---

# 8. Recommended Code Architecture

```text
ikshi/
│
├── app.py
│
├── config/
│   └── settings.py
│
├── camera/
│   └── camera_manager.py
│
├── vision/
│   ├── face_detector.py
│   ├── face_aligner.py
│   └── image_utils.py
│
├── recognition/
│   ├── model.py
│   ├── embedding.py
│   ├── matcher.py
│   └── threshold.py
│
├── enrollment/
│   └── enrollment_service.py
│
├── attendance/
│   ├── attendance_service.py
│   └── session_manager.py
│
├── database/
│   ├── connection.py
│   ├── models.py
│   └── repositories.py
│
├── ui/
│   ├── dashboard.py
│   ├── registration.py
│   └── reports.py
│
├── reports/
│   └── exporter.py
│
├── data/
│   └── attendance.db
│
├── models/
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

# 9. ML Architecture

## Model Selection

Do not select the first  model returned by a search for "face recognition."

The model should be evaluated for:

| Requirement | Importance |
|---|---:|
| Face recognition capability | Critical |
| Embedding/feature output | Critical |
| Local inference | Critical |
| CPU performance | High |
| Accuracy | Critical |
| Model license | Critical |
| Model size | High |
| Documentation | High |
| Community adoption | Medium |

For attendance, prefer a face embedding model over a generic image classifier.

### Desired interface

```text
detect_faces()
      ↓
recognize_face()
      ↓
generate_embedding()
      ↓
match_embedding()
```

The recognition model should be replaceable without rewriting the rest of the application.

---

# 10. OpenCV Responsibilities

OpenCV should primarily handle the real-time vision pipeline:

```text
Webcam
 ↓
Frame capture
 ↓
Resize
 ↓
Color conversion
 ↓
Face detection
 ↓
Face crop
 ↓
Display
```

OpenCV should not contain the entire application's business logic.

---

# 11. Performance Requirements

### Initial Targets

```text
Camera:          720p
Processing:      10–30 FPS
Recognition:     Near real-time
UI response:     < 200 ms for normal actions
Database:        Local SQLite
```

Face recognition does not necessarily need to run on every frame.

Potential optimization:

```text
Camera: 30 FPS

Frame 1  → detection
Frame 2  → tracking
Frame 3  → tracking
Frame 4  → recognition
Frame 5  → tracking
...
```

---

# 12. Recognition Pipeline

A robust pipeline should eventually be:

```text
             CAMERA
                │
                ▼
         Frame preprocessing
                │
                ▼
         Face detection
                │
                ▼
        Quality checking
                │
        ┌───────┴────────┐
        │                │
     Bad face         Good face
        │                │
      Ignore             ▼
                  Face alignment
                        │
                        ▼
                  HF embedding
                        │
                        ▼
                 Normalize vector
                        │
                        ▼
                Similarity search
                        │
                ┌───────┴───────┐
                │               │
             Match           No match
                │               │
                ▼               ▼
           Temporal          UNKNOWN
          confirmation
                │
                ▼
          Attendance
                │
                ▼
             SQLite
```

---

# 13. Face Quality Checks

Before recognition, check:

- Face size
- Blur
- Lighting
- Pose
- Occlusion
- Detection confidence

Example:

```text
Face too small
     ↓
"Move closer"

Face too blurry
     ↓
"Please hold still"

Face good
     ↓
Recognition
```

---

# 14. Anti-Spoofing

Anti-spoofing should be a later phase.

Potential attack:

```text
Registered student
        ↓
Photo/video shown to camera
        ↓
System sees face
        ↓
Incorrectly marks attendance
```

Future pipeline:

```text
Face
 ↓
Liveness check
 ↓
Real person?
 ├── No → Reject
 └── Yes
       ↓
Recognition
       ↓
Attendance
```

Evaluate dedicated liveness/anti-spoofing models separately.

---

# 15. Security & Privacy Requirements

Because this is a biometric system, privacy and security must be considered from the beginning.

## Data Minimization

Prefer storing:

```text
Student ID
+
Face embedding
```

rather than unnecessarily retaining raw photographs.

## Access Control

Admin functions should eventually require authentication.

## Encryption

For production deployments, consider encrypting sensitive biometric data at rest.

## Deletion

Admin should be able to:

```text
Delete student
      ↓
Delete associated embeddings
      ↓
Handle historical attendance according to policy
```

## Consent and Notice

Students should be informed that facial recognition is being used and how their data is handled.

For real deployment, review applicable privacy/data-protection requirements and institutional policies before collecting biometric data.

---

# 16. Error Handling

## Camera Unavailable

```text
Camera unavailable.

[Retry] [Select Camera]
```

## No Face

```text
No face detected.
```

## Multiple Faces

```text
3 faces detected.
```

For MVP, one-person-at-a-time recognition is recommended because it simplifies attendance logic.

## Unknown Face

```text
Face detected
Identity: Unknown
Attendance: Not recorded
```

## Database Failure

```text
Unable to save attendance.

Please contact administrator.
```

---

# 17. Business Rules

### Rule 1

A student can only have one attendance record per session.

### Rule 2

Unknown people never receive attendance.

### Rule 3

A single recognition frame should not automatically mark attendance.

### Rule 4

Recognition must pass a configured similarity threshold.

### Rule 5

Recognition should be temporally stable.

### Rule 6

Inactive students cannot be recognized for attendance.

### Rule 7

Deleting a student must not silently corrupt historical attendance records.

### Rule 8

Changing the recognition model requires re-generating embeddings.

Never compare embeddings generated by incompatible models.

---

# 18. MVP Screens

## Screen 1 — Dashboard

```text
┌─────────────────────────────┐
│       ikshi            │
├─────────────────────────────┤
│                             │
│       CAMERA FEED           │
│                             │
│                             │
├─────────────────────────────┤
│ Recognized: Darshan         │
│ Status: ✓ Present           │
│                             │
│ [Start] [Stop]              │
└─────────────────────────────┘
```

## Screen 2 — Register Student

```text
Register Student

Student ID: [________]
Name:       [________]
Department: [________]

[Capture]
[Save]
```

## Screen 3 — Students

```text
Student Management

ID       Name       Status
1001     Darshan    Active
1002     Rahul      Active

[Add] [Edit] [Delete] [Re-enroll]
```

## Screen 4 — Reports

```text
Attendance Reports

From: [01/09/26]
To:   [30/09/26]

[Generate]

[Export CSV]
```

---

# 19. Non-Functional Requirements

## Reliability

The system should continue operating despite:

- Detection failures
- Unknown faces
- Poor frames
- Temporary camera issues

## Maintainability

ML, camera, database, and UI components must remain modular.

## Portability

Initial target:

- Windows
- Linux

macOS can be supported later.

## Offline Operation

After model downloads, the MVP should work without an internet connection.

Local inference is preferred over sending camera frames to an external inference API.

---

# 20. Testing Strategy

## Software Tests

Test:

- Database insertion
- Database queries
- Duplicate prevention
- Student registration
- Attendance sessions
- CSV export
- Student deletion/deactivation

## ML Tests

Create a test dataset containing:

- Known people
- Unknown people
- Different lighting
- Different angles
- Different distances
- Glasses
- Occlusion
- Different cameras

### False Acceptance

```text
Unknown person
       ↓
Incorrectly recognized as Darshan
```

### False Rejection

```text
Darshan
   ↓
System says Unknown
```

Both should be measured.

---

# 21. Success Metrics

## Recognition

Measure:

- Recognition accuracy
- False acceptance rate
- False rejection rate

Do not claim production accuracy until the selected model has been benchmarked on representative data.

## Attendance

Target:

- Duplicate attendance rate = 0 under normal operation
- Unknown people never automatically marked present
- Successful attendance writes ≥ 99% under normal database operation

## Performance

Target:

```text
Live camera:     smooth
Recognition:     near real-time
UI:              responsive
Database:        immediate local writes
```

---

# 22. Development Roadmap

## Sprint 1 — Environment

Set up:

```text
Python
OpenCV

 libraries
SQLite
```

Deliverable:

> Webcam opens and frames are displayed.

---

## Sprint 2 — Face Detection

Build:

```text
Webcam
 ↓
Face detector
 ↓
Bounding box
```

Deliverable:

> Faces are detected reliably.

---

## Sprint 3 —  Model

Build:

```text
Face
 ↓
HF model
 ↓
Embedding
```

Deliverable:

> You can generate an embedding from a face.

---

## Sprint 4 — Recognition

Build:

```text
Embedding database
       ↓
Similarity search
       ↓
Identity
```

Deliverable:

> Registered people can be recognized.

---

## Sprint 5 — Enrollment

Build:

```text
Register student
       ↓
Capture samples
       ↓
Generate embeddings
       ↓
Save
```

Deliverable:

> New students can be registered without modifying code.

---

## Sprint 6 — Attendance

Build:

```text
Recognized student
       ↓
Temporal confirmation
       ↓
Duplicate check
       ↓
SQLite
```

Deliverable:

> Attendance is automatically recorded.

---

## Sprint 7 — UI

Build:

```text
Dashboard
Registration
Students
Reports
```

Deliverable:

> A non-developer can operate the application.

---

## Sprint 8 — Evaluation

Test:

- Lighting
- Distance
- Camera angle
- Multiple people
- Unknown people
- Recognition threshold
- False matches
- False rejections

Deliverable:

> Measured system performance.

---

## Sprint 9 — Security

Add:

- Admin authentication
- Data protection
- Student deletion
- Model/version tracking
- Logging
- Backup

---

## Sprint 10 — Anti-Spoofing

Add:

```text
Face detection
      ↓
Liveness
      ↓
Recognition
      ↓
Attendance
```

---

# 23. Final MVP Definition

ikshi v1.0 is complete when this flow works:

```text
                ADMIN
                  │
                  ▼
          Register Student
                  │
                  ▼
          Capture Face Samples
                  │
                  ▼
        Generate HF Embeddings
                  │
                  ▼
          Store in Database
                  │
                  │
            CLASS STARTS
                  │
                  ▼
              Webcam
                  │
                  ▼
            OpenCV Frame
                  │
                  ▼
           Detect Face(s)
                  │
                  ▼
          Quality Validation
                  │
                  ▼
          Generate Embedding
                  │
                  ▼
         Compare Embeddings
                  │
             ┌────┴────┐
             │         │
           Match     Unknown
             │         │
             ▼         ▼
        Confirm       Ignore
             │
             ▼
       Already marked?
          /       \
        YES        NO
         │          │
       Ignore       ▼
                Mark Present
                     │
                     ▼
                  SQLite
                     │
                     ▼
                 Dashboard
                     │
                     ▼
                  Reports
```

---

# 24. Recommended Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Camera | OpenCV |
| Face detection | Pretrained CV model |
| Face recognition |  pretrained embedding model |
| ML runtime |  |
| Model management |  Hub |
| Numerical processing | NumPy |
| Database | SQLite |
| GUI | Tkinter |
| Export | CSV |
| Testing | pytest |
| Future API | FastAPI |
| Future frontend | React |

---

# 25. Key Architectural Decision

The most important design decision is to keep **face detection, face recognition, and attendance logic separate**.

Recommended interfaces:

```text
CameraManager
      ↓
FaceDetector
      ↓
FaceRecognizer
      ↓
EmbeddingMatcher
      ↓
AttendanceService
      ↓
AttendanceRepository
      ↓
SQLite
```

This allows you to replace the  model later without rewriting the attendance system.

The model selection should therefore be an explicit evaluation phase rather than an assumption.

---

# 26. UI Architecture — PySide6

## UI Technology Decision

The MVP will use **PySide6 (Qt for Python)** instead of Tkinter.

### Why PySide6

PySide6 is preferred because it provides:

- Modern desktop UI components
- Flexible layouts
- Tables and data views
- Dialogs and forms
- Sidebar/navigation patterns
- Video display widgets
- Styling/theming support
- Strong support for background workers and signals

The UI must remain independent from camera, ML, and database implementation details.

---

## UI Architecture

```text
┌─────────────────────────────────────────────┐
│                 ikshi                  │
├────────────┬────────────────────────────────┤
│ Dashboard  │                                │
│ Attendance │       Main Content Area        │
│ Students   │                                │
│ Sessions   │                                │
│ Reports    │                                │
│ Settings   │                                │
│            │                                │
└────────────┴────────────────────────────────┘
```

The main window contains persistent navigation on the left and a dynamic content area on the right.

---

## UI Screens

The MVP will contain six primary screens:

1. Dashboard
2. Attendance
3. Students
4. Registration
5. Reports
6. Settings

---

## UI-01 — Dashboard

The dashboard is the default screen.

It should immediately show:

- Current attendance session status
- Present count
- Absent count
- Unknown detections
- Last recognized student
- Recent attendance activity
- Quick actions

Example:

```text
┌──────────────────────────────────────────────────────┐
│ ikshi                              Admin ▾      │
├──────────────┬───────────────────────────────────────┤
│ Dashboard    │                                       │
│              │       Attendance Session              │
│ Attendance   │                                       │
│              │ ┌──────────────────┐ ┌─────────────┐ │
│ Students     │ │                  │ │  SESSION    │ │
│              │ │     CAMERA       │ │             │ │
│ Sessions     │ │                  │ │ Present 18  │ │
│              │ │    [Darshan]     │ │ Absent  12  │ │
│ Reports      │ │                  │ │ Unknown  2  │ │
│              │ └──────────────────┘ └─────────────┘ │
│ Settings     │                                       │
│              │ Recent Attendance                     │
│              │ ┌────────┬──────────┬──────────────┐ │
│              │ │ Name   │ Status   │ Time         │ │
│              │ ├────────┼──────────┼──────────────┤ │
│              │ │ Darshan│ Present  │ 09:42        │ │
│              │ │ Rahul  │ Present  │ 09:43        │ │
│              │ └────────┴──────────┴──────────────┘ │
└──────────────┴───────────────────────────────────────┘
```

---

## UI-02 — Attendance Screen

This is the primary operational screen for teachers.

The screen should use a two-panel layout:

- Left: live camera
- Right: session information and attendance

```text
┌────────────────────────────────────────────────────────┐
│ Attendance — CSE-A — Computer Vision                  │
├───────────────────────────────┬────────────────────────┤
│                               │  SESSION                │
│                               │                        │
│          CAMERA               │  Present     18         │
│                               │  Absent      12         │
│       ┌──────────────┐        │  Unknown      2         │
│       │   Darshan    │        │                        │
│       └──────────────┘        │  Last recognized:      │
│                               │  Darshan ✓             │
│                               │                        │
│                               │  Attendance             │
│                               │  ███████████░░          │
│                               │  60%                    │
├───────────────────────────────┴────────────────────────┤
│ [ Pause ]                     [ End Session ]           │
└────────────────────────────────────────────────────────┘
```

The UI must not directly execute model inference or database writes.

---

## UI-03 — Recognition Feedback

The UI must clearly communicate recognition state.

### Recognized

```text
┌────────────────────────┐
│       DARSHAN          │
│                        │
│    ✓ PRESENT           │
│    09:42:31            │
└────────────────────────┘
```

### Unknown

```text
┌────────────────────────┐
│       UNKNOWN          │
│                        │
│    Not registered      │
└────────────────────────┘
```

### Face Detected but Recognition Uncertain

```text
┌────────────────────────┐
│    FACE DETECTED       │
│                        │
│    Please look at      │
│    the camera          │
└────────────────────────┘
```

Recognition feedback should also be visible on the camera frame where practical.

---

## UI-04 — Student Registration

Registration should be implemented as a multi-step wizard.

### Step 1 — Student Information

```text
Register Student

Student ID
[ 2026001 ]

Name
[ Darshan ]

Department
[ Computer Science ▼ ]

Year
[ 3 ▼ ]

                    [ Next → ]
```

### Step 2 — Face Enrollment

```text
Face Enrollment

┌─────────────────────────┐
│                         │
│        CAMERA           │
│                         │
│       [ FACE ]          │
│                         │
└─────────────────────────┘

Samples captured: 3 / 5

Please look straight at the camera.

[ Capture ]
```

### Step 3 — Completion

```text
Enrollment Complete

✓ Face detected
✓ 5 samples captured
✓ Embeddings generated
✓ Quality checks passed

Student: Darshan
ID: 2026001

[ Finish ]
```

---

## UI-05 — Student Management

Use a searchable table.

```text
Students

Search: [ Darshan________________ ]

┌────────┬────────────┬──────────────┬─────────┐
│ ID     │ Name       │ Department   │ Status  │
├────────┼────────────┼──────────────┼─────────┤
│ 1001   │ Darshan    │ CSE          │ Active  │
│ 1002   │ Rahul      │ CSE          │ Active  │
│ 1003   │ Ankit      │ ECE          │ Active  │
└────────┴────────────┴──────────────┴─────────┘

[ + Add Student ] [ Edit ] [ Re-enroll ] [ Disable ]
```

Student details should show:

```text
Student Details

Name:        Darshan
Student ID:  1001
Department:  CSE
Year:        3
Status:      Active

Face enrollment: ✓

[Re-enroll Face]
[Disable Student]
```

---

## UI-06 — Reports

The report screen should provide date, class, and subject filters.

```text
Attendance Reports

From:    [ 01/09/2026 ]
To:      [ 30/09/2026 ]
Class:   [ CSE-A ▼ ]
Subject: [ Computer Vision ▼ ]

[ Generate ]
```

Example output:

```text
┌────────────┬──────────┬─────────────┬─────────────┐
│ Student    │ Present  │ Absent      │ Percentage  │
├────────────┼──────────┼─────────────┼─────────────┤
│ Darshan    │ 18       │ 2           │ 90%         │
│ Rahul      │ 20       │ 0           │ 100%        │
│ Ankit      │ 15       │ 5           │ 75%         │
└────────────┴──────────┴─────────────┴─────────────┘

[ Export CSV ]
```

---

## UI-07 — Settings

Settings should expose system configuration without exposing unnecessary implementation details.

```text
Settings

Camera
────────────────────────────
Camera:        [ Webcam 0 ▼ ]
Resolution:    [ 1280 × 720 ]

Recognition
────────────────────────────
Model:         FaceModel-X
Threshold:     [ 0.80 ]
Confirmation:  [ 3 frames ]

Attendance
────────────────────────────
Duplicate prevention: ✓
Require confirmation:  ✓

[ Save Changes ]
```

The current model name/version should be visible because changing the recognition model may require re-generating all stored embeddings.

---

# 27. UI/Backend Separation

The UI must not contain business logic.

The architecture should be:

```text
                 ┌───────────────┐
                 │   UI Thread   │
                 │   PySide6     │
                 └───────┬───────┘
                         │
                    signals/events
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   Camera Worker                 Recognition Worker
          │                             │
          ▼                             ▼
     OpenCV frames               HF model inference
          │                             │
          └──────────────┬──────────────┘
                         ▼
                  Attendance Service
                         │
                         ▼
                      SQLite
```

The UI is responsible for presentation and user interaction.

The application services are responsible for business decisions.

The ML layer is responsible for computer vision and identity matching.

The database layer is responsible for persistence.

---

# 28. Background Processing

Camera capture and ML inference must not run on the PySide6 UI thread.

Bad architecture:

```text
UI thread
   ↓
Read camera
   ↓
Run  model
   ↓
Compare embeddings
   ↓
Write database
   ↓
Update UI
```

This can freeze the application.

Preferred architecture:

```text
UI Thread
    │
    ├── Camera Worker
    │       └── OpenCV
    │
    └── Recognition Worker
            └── 

Workers
    ↓
Signals / Events
    ↓
UI updates
```

---

# 29. Event-Based Communication

Components should communicate through well-defined events/signals.

Example recognition result:

```python
RecognitionResult(
    student_id=1001,
    name="Darshan",
    similarity=0.91,
    timestamp=...
)
```

The recognition worker emits the result.

The attendance service evaluates:

```text
Is the identity valid?
Is similarity above threshold?
Is the recognition stable?
Is the student active?
Has attendance already been marked?
Is there an active session?
```

If valid, it creates:

```python
AttendanceResult(
    student_id=1001,
    status="PRESENT",
    timestamp=...
)
```

The UI receives the result and updates the display.

The UI should not decide whether someone is actually present.

---

# 30. UI/Backend Contracts

Recommended service boundaries:

```text
CameraManager
      ↓
FaceDetector
      ↓
FaceRecognizer
      ↓
EmbeddingMatcher
      ↓
AttendanceService
      ↓
AttendanceRepository
      ↓
SQLite
```

### UI calls

```text
start_attendance_session()
stop_attendance_session()
register_student()
update_student()
disable_student()
generate_report()
export_report()
```

### Recognition events

```text
face_detected
recognition_started
recognition_result
unknown_face
recognition_error
```

### Attendance events

```text
attendance_marked
attendance_duplicate
attendance_rejected
attendance_error
session_started
session_ended
```

---

# 31. Recommended UI Code Structure

```text
ikshi/
│
├── app.py
│
├── camera/
│   └── camera_manager.py
│
├── vision/
│   ├── face_detector.py
│   ├── face_aligner.py
│   └── image_utils.py
│
├── recognition/
│   ├── model.py
│   ├── embedding.py
│   ├── matcher.py
│   └── threshold.py
│
├── attendance/
│   ├── attendance_service.py
│   └── session_manager.py
│
├── database/
│   ├── connection.py
│   ├── models.py
│   └── repositories.py
│
├── ui/
│   ├── main_window.py
│   │
│   ├── pages/
│   │   ├── dashboard.py
│   │   ├── attendance.py
│   │   ├── students.py
│   │   ├── registration.py
│   │   ├── reports.py
│   │   └── settings.py
│   │
│   ├── widgets/
│   │   ├── camera_view.py
│   │   ├── student_table.py
│   │   ├── status_card.py
│   │   └── attendance_table.py
│   │
│   └── workers/
│       ├── camera_worker.py
│       └── recognition_worker.py
│
├── reports/
│   └── exporter.py
│
├── data/
│   └── attendance.db
│
├── models/
│
└── tests/
```

---

# 32. UI Development Roadmap

## Phase 1 — Camera UI

Build:

```text
Main Window
     ↓
Camera View
     ↓
Face bounding boxes
```

Goal:

> Live webcam video is displayed without blocking the UI.

## Phase 2 — Recognition UI

Add:

```text
Recognition result
     ↓
Name
     ↓
Similarity/status
```

Goal:

> The UI displays recognition results in real time.

## Phase 3 — Attendance UI

Add:

```text
Attendance table
Present/absent counts
Session controls
```

Goal:

> A teacher can run a complete attendance session.

## Phase 4 — Registration UI

Add:

```text
Registration wizard
Face enrollment
Student management
```

Goal:

> New students can be enrolled without modifying code.

## Phase 5 — Reports UI

Add:

```text
Date filters
Class/subject filters
Attendance statistics
CSV export
```

Goal:

> Teachers/admins can retrieve and export attendance.

## Phase 6 — Settings & Security

Add:

```text
Settings
Admin authentication
Model/version information
Data management
```

Goal:

> The application is ready for controlled real-world testing.

---

# 33. UX Principles

The UI should follow these principles:

### 1. Immediate feedback

Every recognition attempt should produce a clear state:

```text
Detecting
Recognizing
Recognized
Unknown
Rejected
Error
```

### 2. Minimal teacher interaction

Normal attendance should require:

```text
Select class
      ↓
Start
      ↓
Monitor
      ↓
End
```

Teachers should not manually click "Present" for every student.

### 3. Prevent accidental actions

Destructive operations such as deleting students or ending sessions should require confirmation.

### 4. Clear system state

Always show:

- Camera status
- Session status
- Recognition status
- Database/save status

### 5. Accessibility

Use:

- Readable text
- Clear labels
- Keyboard navigation where practical
- Non-color-only status indicators

---

# 34. Updated MVP Definition

The MVP is complete when a teacher can:

1. Open ikshi.
2. Select a class and subject.
3. Start an attendance session.
4. See the live webcam feed.
5. See detected faces.
6. Have registered students recognized through the  model.
7. See recognition feedback in the UI.
8. Have recognized students confirmed across multiple frames.
9. Automatically record attendance.
10. Prevent duplicate attendance.
11. See live attendance counts.
12. End the session.
13. View the resulting attendance report.
14. Export the report as CSV.

An admin must also be able to:

1. Register a student.
2. Capture multiple face samples.
3. Generate and store embeddings.
4. View students.
5. Re-enroll a student's face.
6. Disable a student.

---

# 35. Final Product Architecture

```text
                         IKSHI
                              │
                 ┌────────────┴────────────┐
                 │                         │
              PySide6                  Application
                 UI                       Layer
                 │                         │
       ┌─────────┼──────────┐       ┌──────┴───────┐
       │         │          │       │              │
   Dashboard Attendance Students  Session      Attendance
       │         │          │      Manager        Service
       │         │          │       │              │
       └─────────┴──────────┘       └──────┬───────┘
                                           │
                                           ▼
                                  Recognition Layer
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                           OpenCV                 
                              │                     + 
                              ▼                         │
                       Face Detection                   │
                              │                         │
                              └────────────┬────────────┘
                                           ▼
                                      Embeddings
                                           │
                                           ▼
                                    Similarity Match
                                           │
                                           ▼
                                         SQLite
                                           │
                                           ▼
                                        Reports
```

The central architectural rule is:

> **PySide6 is responsible for presentation, OpenCV is responsible for camera/vision processing,  is responsible for the pretrained ML model, the Attendance Service is responsible for attendance decisions, and SQLite is responsible for persistence.**

This separation allows each part to be developed, tested, and replaced independently.

---

# OpenCV SFace Implementation Specification

## Recognition API

The recognition implementation must use:

```python
cv2.FaceRecognizerSF
```

Core operations:

```python
recognizer.alignCrop(...)
recognizer.feature(...)
recognizer.match(...)
```

The exact argument signatures must follow the installed OpenCV version.

## Recognition Pipeline

```text
Camera Frame
     ↓
OpenCV Face Detector
     ↓
Detected Face
     ↓
SFace alignCrop()
     ↓
SFace feature()
     ↓
Stored SFace features
     ↓
Cosine similarity
     ↓
Threshold
     ↓
Known / Unknown
```

## Enrollment

Each registered student should have multiple SFace feature vectors:

```text
student
 ├── feature_01
 ├── feature_02
 ├── feature_03
 ├── feature_04
 └── feature_05
```

This improves robustness to normal changes in pose, expression, and lighting.

## Matching

Use one comparison metric consistently.

Recommended MVP:

```text
Cosine similarity
```

The threshold must be calibrated experimentally. A value shown in UI examples is illustrative only and must not be treated as a validated production threshold.

## Model Compatibility

Every stored feature must record:

```text
model_name
model_version
metric
```

If the SFace model changes, all stored student features must be regenerated before matching with the new model.

## Local Model Storage

```text
models/
├── face_detection/
│   └── detector model files
└── sface/
    └── SFace model file
```

The project must document the exact model files, source, version, checksum where practical, and license in:

```text
models/README.md
```

No runtime dependency on an online model hub is required.

---

# Dependency Policy

The MVP dependency list should remain minimal:

```text
opencv-contrib-python
numpy
PySide6
pytest
```

Use the appropriate OpenCV package/version required by the selected SFace API and verify that `cv2.FaceRecognizerSF` is available.

Do not add ML frameworks merely for face recognition.

---

# Updated Architecture

```text
                         IKSHI
                              │
                 ┌────────────┴────────────┐
                 │                         │
              PySide6                  Application
                 UI                       Layer
                 │                         │
       ┌─────────┼──────────┐       ┌──────┴───────┐
       │         │          │       │              │
   Dashboard Attendance Students  Session      Attendance
       │         │          │      Manager        Service
       │         │          │       │              │
       └─────────┴──────────┘       └──────┬───────┘
                                           │
                                           ▼
                                  OpenCV Recognition
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                       OpenCV Detector               SFace
                              │                         │
                              ▼                         ▼
                         Face Box                 Feature Vector
                              │                         │
                              └────────────┬────────────┘
                                           ▼
                                    Similarity Match
                                           │
                                           ▼
                                         SQLite
                                           │
                                           ▼
                                        Reports
```

## Architectural Rule

> **PySide6 handles presentation. OpenCV handles camera and computer vision. SFace handles face feature extraction and recognition. NumPy handles numerical data. Application services make attendance decisions. SQLite stores application data.**

No Hugging Face or PyTorch component is part of this architecture.
