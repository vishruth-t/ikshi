MOBILE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#090D16">
    <title>FaceAttend Mobile</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            background-color: #090D16;
            color: #F8FAFC;
            padding: 16px;
            padding-bottom: 80px;
            font-size: 14px;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 16px;
            border-bottom: 1px solid #1E293B;
            margin-bottom: 16px;
        }
        .brand {
            font-size: 18px;
            font-weight: 800;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-active {
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .status-standby {
            background: rgba(148, 163, 184, 0.12);
            color: #94A3B8;
            border: 1px solid rgba(148, 163, 184, 0.25);
        }
        .card-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 16px;
        }
        .card {
            background: linear-gradient(180deg, #1E293B 0%, #111827 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px;
        }
        .card-label {
            font-size: 11px;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .card-value {
            font-size: 24px;
            font-weight: 800;
            color: #FFFFFF;
        }
        .card-sub {
            font-size: 11px;
            color: #64748B;
            margin-top: 2px;
        }
        .control-panel {
            background: #111827;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 16px;
        }
        .btn {
            width: 100%;
            padding: 14px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 700;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: opacity 0.2s;
        }
        .btn:active {
            opacity: 0.8;
            transform: scale(0.98);
        }
        .btn-green {
            background: linear-gradient(90deg, #059669 0%, #10B981 100%);
            color: white;
        }
        .btn-red {
            background: linear-gradient(90deg, #DC2626 0%, #EF4444 100%);
            color: white;
        }
        .section-title {
            font-size: 15px;
            font-weight: 800;
            color: #F1F5F9;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .feed-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .feed-item {
            background: #111827;
            border: 1px solid #1E293B;
            border-radius: 10px;
            padding: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .avatar {
            width: 34px;
            height: 34px;
            border-radius: 17px;
            background: rgba(56, 189, 248, 0.15);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 12px;
            margin-right: 10px;
        }
        .student-info {
            flex: 1;
        }
        .student-name {
            font-weight: 700;
            font-size: 13px;
            color: #F8FAFC;
        }
        .student-sub {
            font-size: 11px;
            color: #94A3B8;
        }
        .feed-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 8px;
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .empty-state {
            text-align: center;
            padding: 28px 16px;
            color: #64748B;
            font-size: 13px;
            background: #111827;
            border: 1px dashed #1E293B;
            border-radius: 12px;
        }
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            z-index: 100;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .modal-box {
            background: #161F30;
            border: 1px solid #334155;
            border-radius: 14px;
            width: 100%;
            max-width: 360px;
            padding: 20px;
        }
        .input-group {
            margin-bottom: 12px;
        }
        .input-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #94A3B8;
            margin-bottom: 4px;
        }
        .input-field {
            width: 100%;
            background: #090D16;
            border: 1px solid #334155;
            padding: 10px 12px;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            outline: none;
        }
        .input-field:focus {
            border-color: #3B82F6;
        }
        .modal-actions {
            display: flex;
            gap: 10px;
            margin-top: 16px;
        }
        .btn-secondary {
            background: #1E293B;
            color: #CBD5E1;
            border: 1px solid #334155;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="brand">⚡ FaceAttend</div>
        <div id="statusBadge" class="status-badge status-standby">○ Standby</div>
    </div>

    <!-- Active Session Overview -->
    <div class="control-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
                <div id="sessionClass" style="font-weight: 800; font-size: 15px; color: #FFFFFF;">No Active Session</div>
                <div id="sessionSub" style="font-size: 12px; color: #94A3B8;">Start attendance from your phone below</div>
            </div>
        </div>
        <button id="btnSessionAction" class="btn btn-green" onclick="handleSessionBtnClick()">
            ▶ Start Attendance Session
        </button>
    </div>

    <!-- Stats Grid -->
    <div class="card-grid">
        <div class="card" style="border-top: 2px solid #10B981;">
            <div class="card-label">Verified Present</div>
            <div id="statPresent" class="card-value">0</div>
            <div id="statPercent" class="card-sub">0.0% of class</div>
        </div>
        <div class="card" style="border-top: 2px solid #8B5CF6;">
            <div class="card-label">Total Enrolled</div>
            <div id="statTotal" class="card-value">0</div>
            <div class="card-sub">Directory total</div>
        </div>
    </div>

    <!-- Live Verified Attendance Roll -->
    <div class="section-title">
        <span>📋 Live Attendance Roll</span>
        <span id="feedCount" style="font-size: 11px; color: #38BDF8; font-weight: 700;">0 Verified</span>
    </div>
    <div id="feedList" class="feed-list">
        <div class="empty-state">No attendance recorded yet for this session.</div>
    </div>

    <!-- Start Session Modal -->
    <div id="startModal" class="modal-overlay">
        <div class="modal-box">
            <h3 style="margin-bottom: 14px; font-size: 16px;">Start Attendance Session</h3>
            <div class="input-group">
                <label class="input-label">Class / Room</label>
                <input id="modalClass" class="input-field" type="text" placeholder="e.g. CS-101" value="CS-101">
            </div>
            <div class="input-group">
                <label class="input-label">Subject Name</label>
                <input id="modalSubject" class="input-field" type="text" placeholder="e.g. Computer Vision" value="Computer Vision">
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="closeStartModal()">Cancel</button>
                <button class="btn btn-green" onclick="confirmStartSession()">Start</button>
            </div>
        </div>
    </div>

    <script>
        let isSessionActive = false;
        let lastRecordCount = 0;

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                isSessionActive = data.session_active;
                const badge = document.getElementById('statusBadge');
                const btn = document.getElementById('btnSessionAction');
                const title = document.getElementById('sessionClass');
                const sub = document.getElementById('sessionSub');
                
                if (data.session_active) {
                    badge.className = 'status-badge status-active';
                    badge.innerText = '● Live Active';
                    btn.className = 'btn btn-red';
                    btn.innerText = '⏹ End Attendance Session';
                    title.innerText = data.class_name || 'Active Session';
                    sub.innerText = `${data.subject || ''} • Session #${data.session_id}`;
                } else {
                    badge.className = 'status-badge status-standby';
                    badge.innerText = '○ Standby';
                    btn.className = 'btn btn-green';
                    btn.innerText = '▶ Start Attendance Session';
                    title.innerText = 'No Active Session';
                    sub.innerText = 'Tap below to launch a new session';
                }

                document.getElementById('statPresent').innerText = data.present_count;
                document.getElementById('statTotal').innerText = data.total_enrolled;
                const pct = data.total_enrolled > 0 ? ((data.present_count / data.total_enrolled) * 100).toFixed(1) : '0.0';
                document.getElementById('statPercent').innerText = `${pct}% of class`;

                // Fetch live records
                if (data.session_active) {
                    fetchLiveRoll(data.session_id);
                } else {
                    document.getElementById('feedList').innerHTML = '<div class="empty-state">No session is currently active.</div>';
                    document.getElementById('feedCount').innerText = '0 Verified';
                }
            } catch (err) {
                console.error('Status fetch error:', err);
            }
        }

        async function fetchLiveRoll(sessionId) {
            try {
                const res = await fetch('/api/live-roll');
                const records = await res.json();
                
                document.getElementById('feedCount').innerText = `${records.length} Verified`;
                const feed = document.getElementById('feedList');
                
                if (records.length === 0) {
                    feed.innerHTML = '<div class="empty-state">Waiting for students in front of camera...</div>';
                    return;
                }

                feed.innerHTML = records.map(r => {
                    const initials = (r.name || 'ST').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                    const time = (r.marked_at || '').split('T').pop().substring(0, 8);
                    const sim = Math.round((r.similarity || 0) * 100);
                    return `
                        <div class="feed-item">
                            <div style="display: flex; align-items: center;">
                                <div class="avatar">${initials}</div>
                                <div class="student-info">
                                    <div class="student-name">${r.name}</div>
                                    <div class="student-sub">${r.student_number || ''} • ${time}</div>
                                </div>
                            </div>
                            <div class="feed-badge">${sim}% Match</div>
                        </div>
                    `;
                }).join('');
            } catch (err) {
                console.error('Roll fetch error:', err);
            }
        }

        function handleSessionBtnClick() {
            if (isSessionActive) {
                if (confirm('Are you sure you want to end this attendance session?')) {
                    endSession();
                }
            } else {
                document.getElementById('startModal').style.display = 'flex';
            }
        }

        function closeStartModal() {
            document.getElementById('startModal').style.display = 'none';
        }

        async function confirmStartSession() {
            const cls = document.getElementById('modalClass').value.trim() || 'CS-101';
            const subj = document.getElementById('modalSubject').value.trim() || 'General';
            closeStartModal();

            try {
                await fetch('/api/session/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({class_name: cls, subject: subj})
                });
                fetchStatus();
            } catch (err) {
                alert('Failed to start session: ' + err);
            }
        }

        async function endSession() {
            try {
                await fetch('/api/session/stop', {method: 'POST'});
                fetchStatus();
            } catch (err) {
                alert('Failed to end session: ' + err);
            }
        }

        // Poll every 1.5 seconds for real-time mobile updates
        setInterval(fetchStatus, 1500);
        fetchStatus();
    </script>
</body>
</html>
"""
