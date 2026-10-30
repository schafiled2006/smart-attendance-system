# Smart Attendance System - Complete Frontend Specification

## 📊 Project Overview
**Backend URL**: `http://127.0.0.1:8000` (FastAPI server)  
**Frontend Base**: `http://localhost:5173` (React Vite default)  
**CORS**: Already configured for `localhost:5173` - no changes needed  
**Authentication**: **Simulated** - any username accepted, no auth tokens required  
**Data Format**: JSON, ISO timestamps, Persian dates via jdatetime  

---

## 🗂️ Page/Component Structure

### 1. Dashboard/Home Page
- Layout with sidebar navigation
- Quick stats cards (total students, active sessions, today's attendance)
- Links to main sections
- Status indicator (server running/offline)

### 2. Students Management Page
- **Student List Table** with pagination/search
  - Columns: Student ID, Full Name, Major, Term, Actions
- **Add Student Form**
  - Fields: Student ID (unique), Full Name, Major, Term
  - File upload: 3-5 images (drag & drop or browse)
  - Submit buttons:
    - "Save Student Meta" → `POST /api/students`
    - "Process Images" → `POST /api/students/{id}/enroll`
- **Error/Success Toasts** for all operations

### 3. Courses Management Page
- **Course List Table** with pagination
  - Columns: Course Code, Title, Teacher, Students Count, Actions
- **Add Course Form**
  - Fields: Course Code (UNIQUE), Title, Teacher
- **Assign Students to Course** (if needed)

### 4. Sessions Page
- **Active Session Indicator** (shows if session is running)
- **Session List** with pagination
  - Columns: Session ID, Course, Start Time, Status, Duration, Actions
- **Start New Session**
  - Select course from dropdown
  - Set late threshold (minutes, default 10)
  - Optional note
  - Button: "Start Session" → `POST /api/sessions/start`
- **Close Session**
  - Show active sessions
  - Button: "Close Session"

### 5. Attendance Page (Main Interface)
- **Camera Preview Area**
  - Video stream from laptop camera or phone (IP Webcam)
  - Toggle: Laptop Camera / Phone Camera / Manual
- **Recognized Faces List**
  - Real-time updating grid
  - Each face: Student ID, Name, Confidence Score
  - Buttons: "Mark Present", "Mark Late", "Skip"
- **Manual Attendance Panel**
  - Student ID input
  - Status selector: Present / Late / Absent
  - Button: "Mark Attendance"
- **Session Timer**
  - Countdown from session start
  - Late threshold indicator (turns red after threshold)
- **Attendance History** for current session
  - List of all students with their status
  - Filter by: Present / Late / Absent

### 6. Reports Page
- **Session Selection Dropdown**
  - Load sessions from backend
- **Excel Export Button**
  - "Generate Excel Report"
  - Shows progress spinner
  - Download link after completion
- **Report Summary Section**
  - Total students in session
  - Present count
  - Late count
  - Absent count
- **Download History** (previous reports)
  - List with download links
  - File names with Jalali dates

### 7. Login/Auth Page (Simulated)
- Since authentication is simulated, this can be minimal
- Or just auto-login on start
- Display: "System: Smart Attendance Backend v1.0"
- Connection status indicator

---

## 🔌 API Integration Details

### Base URL
```
const API_BASE = 'http://127.0.0.1:8000';
```

### 1. Students Endpoints

**POST /api/students**
```javascript
// Request
{
  "student_id": "S12345",       // required, unique
  "full_name": "Ali Rezaei",     // required
  "major": "Computer Science",   // optional
  "term": "90"                   // optional
}

// Success Response
{
  "id": 1,
  "student_id": "S12345",
  "full_name": "Ali Rezaei",
  "major": "Computer Science",
  "term": "90",
  "embedding_file": "embeddings/S12345.npy",
  "created_at": "2026-10-24T15:30:00"
}
```

**POST /api/students/{id}/enroll**
```javascript
// Request
{
  "image_folder_path": "C:/known_faces/S12345/"  // path on server
}

// Success Response
{
  "success": true,
  "message": "Embedding rebuilt successfully",
  "rebuilt": 5,
  "failed": 0
}
```

### 2. Courses Endpoints

**GET /api/courses**
```javascript
// Response: [{id, course_code, title, teacher, created_at}, ...]
```

**POST /api/courses**
```javascript
// Request
{
  "course_code": "CS101",       // required, UNIQUE
  "title": "Introduction AI",    // required
  "teacher": "Dr. Smith"         // optional
}
```

### 3. Sessions Endpoints

**POST /api/sessions/start**
```javascript
// Request
{
  "course_id": 1,               // required
  "late_threshold_minutes": 10, // optional, default 10
  "note": ""                    // optional
}

// Response
{
  "session_id": "session_20261024153000",
  "course_id": 1,
  "start_time": "2026-10-24T15:30:00",
  "status": "active",
  "late_threshold_minutes": 10,
  "note": "",
  "created_at": "2026-10-24T15:30:00"
}
```

**POST /api/sessions/{id}/close**
```javascript
// Request: none (just URL parameter)
// Response
{
  "success": true,
  "message": "Session closed"
}
```

**GET /api/sessions/active**
```javascript
// Response
{
  "session_id": "session_20261024153000",
  "course_id": 1,
  "start_time": "2026-10-24T15:30:00",
  "status": "active",
  "late_threshold_minutes": 10
}
```

### 4. Attendance Endpoints

**POST /api/attendance/recognize**
```javascript
// Request
{
  "recognized_list": [
    {"student_id": "S12345", "full_name": "Ali Rezaei", "confidence": 0.92}
  ],
  "camera_source": "laptop"   // "laptop" | "phone" | "manual"
}

// Success Response (for each recognition)
{
  "results": [
    {
      "student_id": "S12345",
      "full_name": "Ali Rezaei",
      "status": "present",     // "present" | "late" | "absent"
      "check_in_time": "2026-10-24T15:35:00",
      "confidence": 0.92,
      "message": "حضور حاضر ثبت شد"
    }
  ],
  "message": "Processing complete"
}
```

**POST /api/attendance/manual**
```javascript
// Request
{
  "student_id": "S12345",
  "status": "present"    // "present" | "late" | "absent"
}

// Response (same structure as recognize success)
```

### 5. Reports Endpoints

**GET /api/reports/session/{id}/excel**
```javascript
// Response
{
  "success": true,
  "file_path": "/attendance_system/reports/raport_session_20261024_1403_07_01.xlsx",
  "filename": "raport_session_20261024_1403_07_01.xlsx",
  "summary": {
    "session_id": "session_20261024153000",
    "course_title": "Introduction to AI",
    "date_jalali": "1403/07/01",
    "date_gregorian": "2026/10/24",
    "total_students": 45,
    "present_count": 38,
    "late_count": 5,
    "absent_count": 2,
    "records": [  // array of student records
      {
        "student_id": "S12345",
        "full_name": "Ali Rezaei",
        "major": "Computer Science",
        "term": "90",
        "status": "present",
        "check_in_time": "15:35:00",
        "confidence": 0.92
      }
    ]
  },
  "message": "Excel generated successfully"
}
```
- **Action**: Download the file from `file_path` or use `filename` with base URL
- **Technology**: openpyxl + jdatetime on backend

**GET /api/reports/daily**
```javascript
// Response: similar structure to session report but for all today's sessions
```

---

## 📱 Camera & Face Recognition Integration

### Video Stream Setup
```javascript
// Use MediaStream API for laptop camera
const constraints = {
  video: {
    facingMode: 'environment',  // for phone camera if supported
    width: { ideal: 640 },
    height: { ideal: 480 }
  }
};

const stream = await navigator.mediaStream.getUserMedia(constraints);
videoElement.srcObject = stream;

// Or for IP Webcam phone: just use the URL
// const phoneStream = new RTSPSource('http://192.168.x.x:8080/video');
```

### Face Recognition Processing
```javascript
// When user clicks "Analyze Frame"
async function analyzeFrame() {
  // Draw current frame from video
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  // Convert to dataURL or blob
  const dataURL = canvas.toDataURL('image/jpeg', 0.8);
  
  // Send to backend
  const response = await fetch(`${API_BASE}/api/attendance/recognize`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      recognized_list: [],  // Will be populated by backend processing
      camera_source: 'laptop'
    })
  });
  
  const result = await response.json();
  displayResults(result.results);
}
```

**Note**: The backend `face_engine.py` handles the actual face detection/recognition. The frontend just sends the recognition results (student_id, full_name, confidence) that were obtained from client-side or separate server-side face detection.

### Alternative: Client-side Face Detection
If you want to do face detection in the browser:
- Use `face-recognition-js` or `opencv4webassembly`
- Or integrate with WebCNN APIs
- Send only bounding boxes + embeddings to backend for final matching

---

## 📊 State Management (React Context Example)

```javascript
// attendance-context.js
import React, { createContext, useContext, useState, useEffect } from 'react';

const AttendanceContext = createContext();

export const AttendanceProvider = ({ children }) => {
  const [session, setSession] = useState(null);
  const [students, setStudents] = useState([]);
  const [recognizedFaces, setRecognizedFaces] = useState([]);
  const [cameraStream, setCameraStream] = useState(null);
  const [status, setStatus] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Load active session on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/sessions/active`)
      .then(res => res.json())
      .then(setSession)
      .catch(console.error);
  }, []);
  
  // Load students list
  useEffect(() => {
    fetch(`${API_BASE}/api/students`)
      .then(res => res.json())
      .then(setStudents)
      .catch(console.error);
  }, []);
  
  return (
    <AttendanceContext.Provider value={{session, students, recognizedFaces, cameraStream, status, isProcessing}}>
      {children}
    </AttendanceContext.Provider>
  );
};

export const useAttendance = () => useContext(AttendanceContext);
```

---

## 🎨 UI/UX Specifications

### Color Scheme (suggested)
- **Primary**: #2563EB (FastAPI/theme blue)
- **Success**: #10B981 (present green)
- **Warning**: #F59E0B (late amber)
- **Error**: #EF4444 (absent red)
- **Background**: #F8FAFC (light gray)
- **Card**: #FFFFFF white with subtle shadow

### Status Color Coding
| Status | Color | Background |
|--------|-------|------------|
| Present | #059669 | #DCFCE7 |
| Late | #D97706 | #FEF3C7 |
| Absent | #DC2626 | #FEE2E2 |

### Typography
- Font family: Inter, system-ui, -apple-system, sans-serif
- Headings: font-medium, font-semibold
- Body: font-normal, text-sm sizes

### Responsive Breakpoints
- Mobile: <640px (stack columns, simplified layout)
- Tablet: 640px-1024px (two-column layouts)
- Desktop: >1024px (full feature set)

---

## ⚠️ Error Handling Patterns

### API Error Responses
```javascript
// Expected error format from backend
{
  "detail": "Error message in English or Persian"
}

// Common error cases
// 400 - Bad request (invalid input)
// 404 - Not found (session/student not found)
// 409 - Conflict (already registered in session)
// 500 - Server error
```

### Frontend Error Handling
```javascript
try {
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorData = await response.json();
    showToast(errorData.detail || 'An error occurred', 'error');
    throw errorData;
  }
  const data = await response.json();
  return data;
} catch (error) {
  // Handle network errors, timeouts, etc.
  showToast('Connection failed. Please try again.', 'error');
}
```

### Validation Before API Calls
- Student ID: must be unique, format: `S` + numbers
- Image upload: minimum 3, maximum 5 files, valid extensions: jpg, jpeg, png
- Student name: not empty, max 100 characters
- Late threshold: positive integer (1-60 minutes)

---

## 📝 Form Components Specification

### Student Add Form
```jsx
<StudentAddForm
  onSave={async (data) => {
    // Call POST /api/students
    const result = await fetch(`${API_BASE}/api/students`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {'Content-Type': 'application/json'}
    });
    const json = await result.json();
    if (result.ok) showToast('Student registered', 'success');
    else showToast(json.detail || 'Failed', 'error');
  }}
  onEnroll={async (studentId, files) => {
    // Call POST /api/students/{id}/enroll
    const formData = new FormData();
    files.forEach(f => formData.append('images', f));
    formData.append('student_id', studentId);
    
    const result = await fetch(`${API_BASE}/api/students/${studentId}/enroll`, {
      method: 'POST',
      body: formData
    });
    // handle response
  }}
/>
```

### Course Add Form
```jsx
<CourseAddForm
  onSubmit={async (data) => {
    const result = await fetch(`${API_BASE}/api/courses`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {'Content-Type': 'application/json'}
    });
    // handle response
  }}
/>
```

### Session Start Form
```jsx
<SessionStartForm
  onSubmit={async (data) => {
    // data: {course_id, late_threshold_minutes, note}
    const result = await fetch(`${API_BASE}/api/sessions/start`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {'Content-Type': 'application/json'}
    });
    // handle response, show session_id, start timer
  }}
/>
```

### Manual Attendance Form
```jsx
<ManualAttendanceForm
  onSubmit={async (data) => {
    // data: {student_id, status}
    const result = await fetch(`${API_BASE}/api/attendance/manual`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {'Content-Type': 'application/json'}
    });
    // handle response, update UI
  }}
/>
```

### Excel Export Button
```jsx
<ExcelExportButton
  sessionId={currentSession.id}
  onDownload={async () => {
    const result = await fetch(`${API_BASE}/api/reports/session/${currentSession.id}/excel`);
    const data = await result.json();
    
    if (data.success) {
      // Trigger download
      const a = document.createElement('a');
      a.href = `${API_BASE}${data.file_path}`;
      a.download = data.filename;
      a.click();
      showToast('Report downloaded', 'success');
    } else {
      showToast(data.detail || 'Failed', 'error');
    }
  }}
/>
```

---

## 📈 Sample Data Flow

### Complete User Journey: New Student Registration

1. **User opens Students page**
2. **Fills form**: Student ID: `S99999`, Name: `محمد احمدی`, Major: `Information Technology`, Term: `91`
3. **Uploads 3 images** (drags 3 jpg files or clicks browse)
4. **Clicks "Save Student Meta"** → `POST /api/students` → success → shows student in list
5. **Clicks "Process Images"** → `POST /api/students/S99999/enroll` → processes 3 images → saves embedding → shows success
6. **Student now appears in dropdowns** for course assignments

### Complete User Journey: Attendance Taking

1. **User opens Attendance page**
2. **Selects camera** (laptop or phone IP Webcam URL)
3. **Video stream starts** - faces detected in real-time
4. **System recognizes faces** - shows list with confidence scores
5. **User clicks "Mark Present"** for each recognized student
6. **System auto-saves** to database via `POST /api/attendance/recognize`
7. **Timer shows** elapsed time vs late threshold
8. **After session**: User clicks "Close Session"
9. **User generates report**: `GET /api/reports/session/{id}/excel`
10. **Downloads Excel file** with all attendance data + Jalali date

### Complete User Journey: Course Management

1. **User opens Courses page**
2. **Clicks "Add Course"**
3. **Fills form**: Course Code: `CS101`, Title: `Introduction to AI`, Teacher: `Dr. Smith`
4. **Clicks "Create"** → `POST /api/courses` → success
5. **Course appears in dropdowns** for session creation
6. **User can now create sessions** for this course

---

## 🔧 Configuration & Environment Variables

### Frontend .env (React Vite)
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_APP_NAME=Smart Attendance System
VITE_ENABLE_LOGGING=false
```

### Backend .env (already configured in config.py)
```python
FACE_TOLERANCE = 0.55
FACE_MODEL = "hog"                 # hog for CPU Windows
PROCESS_EVERY_N_FRAMES = 2
DEFAULT_LATE_THRESHOLD = 10
PHONE_CAMERA_URL = "http://192.168.x.x:8080/video"  # update with actual phone IP
DB_PATH = "data/attendance.db"
```

### CORS Configuration (already in main.py)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📦 Dependencies for Frontend

```bash
# React Router for navigation
npm install react-router-dom

# State management (optional, if not using Redux)
npm install @reduxjs/toolkit react-redux

# API client (alternative to fetch)
npm install axios

# Date handling with Persian support
npm install @iranianjs/jdatepicker  # or use jdatetime CDN

# Toast notifications
npm install react-hot-toast

# Image crop/upload
npm install react-dropzone

# Optional: Camera access utilities
npm install mediaelement

# Charting for statistics (if needed)
npm install chart.js react-chartjs-2
```

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] Student form validation
- [ ] Course creation with duplicate code rejection
- [ ] Session start/close flow
- [ ] Excel download functionality

### Integration Tests
- [ ] Full student registration flow
- [ ] Attendance recognition cycle
- [ ] Report generation and download
- [ ] Camera stream start/stop

### Manual Testing
- [ ] Register student with 3+ images
- [ ] Start session, verify late threshold logic
- [ ] Recognize face (mock data or real camera)
- [ ] Generate Excel report, verify Persian dates
- [ ] Test with different browsers (Chrome, Firefox, Edge)
- [ ] Test responsive design (mobile/tablet/desktop)

---

## 🚀 Deployment Notes

### Development
```bash
# Start backend
cd attendance_system/backend
python main.py

# Start frontend  
cd frontend
npm run dev
```
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:5173`
- CORS auto-configured between them

### Build for Production
```bash
npm run build
# Serve static files with any web server (nginx, serve, etc.)
```

### Important Notes
- **Backend must be running** for frontend to work
- **No authentication** needed - system simulates any user
- **Camera permission** required from user browser
- **Image processing** may take a few seconds per student
- **Excel files** generated on server, downloaded by client
- **Persian dates** handled via jdatetime on both sides

---

## 📞 Support & troubleshooting

### Common Issues

1. **CORS error**: Ensure both frontend and backend running, no manual CORS config needed
2. **Camera not accessing**: Check browser permissions, HTTPS requirement for local cameras
3. **Face not recognized**: 
   - Ensure good lighting
   - Student images should be clear, front-facing, no glasses if possible
   - Tolerance is 0.55 (configurable in backend config.py)
4. **Excel download fails**: Check backend file path, ensure reports directory has write permission
5. **Persian dates show as garbage**: Ensure jdatetime library loaded correctly, server timezone set properly
6. **Student already registered error**: Student already in database - use different ID or update existing

### Debugging Tools
- Swagger docs: `http://127.0.0.1:8000/docs`
- Use browser DevTools Network tab to inspect API calls
- Check console for fetch errors
- Backend logs in console where `python main.py` running

---

## 📐 Final Checklist for Frontend Developer

- [ ] Create React Vite project
- [ ] Configure `VITE_API_BASE_URL` in .env
- [ ] Implement all 7 pages/components listed above
- [ ] Add all API integration code (18 endpoints)
- [ ] Add camera/video stream setup
- [ ] Add face recognition call integration
- [ ] Add Excel export functionality
- [ ] Add Persian date formatting (jdatetime)
- [ ] Add toast notifications for all success/error cases
- [ ] Test complete user flows
- [ ] Verify responsive design
- [ ] Document any additional requirements

---

## 📞 Final Deliverable

That's the complete frontend specification. Give this to your frontend developer and they should be able to build the complete React/Vite application that works with the backend I created. All endpoints, data formats, and workflows are documented. The key points are:

1. **API Base**: `http://127.0.0.1:8000`
2. **CORS**: Already configured for `localhost:5173`
3. **No auth needed** - any username works
4. **Camera required** for face recognition feature
5. **Excel reports** include Persian dates
6. **3+ student images** minimum for registration

Good luck with the frontend development!