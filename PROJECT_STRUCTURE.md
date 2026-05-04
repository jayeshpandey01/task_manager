# Project Structure Overview

## Frontend Architecture

```
client/src/
├── pages/
│   ├── Layout.jsx                    ← Auth flow, blocked screen, role check
│   ├── Dashboard.jsx                 ← Branches by role (ADMIN/MEMBER)
│   ├── AdminDashboard.jsx       [NEW] ← Admin stats & team performance panel
│   ├── MemberDashboard.jsx      [NEW] ← Personal tasks & GitHub timer
│   ├── Team.jsx                      ← Block/score controls (admin only)
│   ├── TaskDetails.jsx               ← Task accept button + timer
│   └── ... (other existing pages)
│
├── components/
│   ├── TaskTimer.jsx            [NEW] ← Live countdown timer for GitHub tasks
│   ├── Navbar.jsx
│   ├── Sidebar.jsx
│   ├── CreateProjectDialog.jsx
│   ├── CreateTaskDialog.jsx
│   ├── InviteMemberDialog.jsx
│   ├── ProjectOverview.jsx
│   ├── RecentActivity.jsx
│   ├── StatsGrid.jsx
│   └── ... (other existing components)
│
├── features/
│   ├── workspaceSlice.js             ← Redux state (+ updateMember action)
│   ├── themeSlice.js
│   └── ... (other slices)
│
├── hooks/
│   ├── useRole.js                    ← Checks if user is ADMIN
│   └── ... (other hooks)
│
├── configs/
│   └── api.js                        ← Axios instance for API calls
│
└── ... (other directories)
```

## Backend Architecture

```
server/
├── controllers/
│   ├── workspaceController.js        ← getUserWorkspaces, addMember, [NEW] blockMember, updateMemberScore
│   ├── taskController.js             ← createTask, updateTask, deleteTask, [NEW] acceptTask
│   ├── projectController.js
│   ├── commentController.js
│   └── ... (other controllers)
│
├── routes/
│   ├── workspaceRoutes.js            ← [NEW] PUT /member/:memberId/block, PUT /member/:memberId/score
│   ├── taskRoutes.js                 ← [NEW] PUT /:id/accept
│   ├── projectRoutes.js
│   └── ... (other routes)
│
├── middlewares/
│   ├── authMiddleware.js             ← Clerk auth verification
│   └── ... (other middlewares)
│
├── configs/
│   └── prisma.js                     ← Prisma client
│
├── prisma/
│   └── schema.prisma                 ← Database schema [UPDATED] score, isBlocked, isAccepted, acceptedAt
│
├── server.js                         ← Express app setup
└── ... (other files)
```

## Data Flow

### Admin Blocking Member

```
Team.jsx (handleBlock)
    ↓
api.put(/api/workspaces/member/:memberId/block)
    ↓
workspaceController.blockMember()
    ↓
prisma.workspaceMember.update({ isBlocked: !member.isBlocked })
    ↓
dispatch(updateMember(data.member))
    ↓
Redux state updated
    ↓
UI re-renders (Blocked status shown)
```

### Admin Setting Member Score

```
Team.jsx or AdminDashboard.jsx (handleScoreSave)
    ↓
api.put(/api/workspaces/member/:memberId/score, { score })
    ↓
workspaceController.updateMemberScore()
    ↓
prisma.workspaceMember.update({ score })
    ↓
dispatch(updateMember(data.member))
    ↓
Redux state updated
    ↓
UI re-renders (Score badge updated)
```

### Member Accepting Task

```
MemberDashboard.jsx or TaskDetails.jsx (handleAccept)
    ↓
api.put(/api/tasks/:taskId/accept)
    ↓
taskController.acceptTask()
    ↓
prisma.task.update({ isAccepted: true, acceptedAt: new Date() })
    ↓
dispatch(updateTask(data.task))
    ↓
Redux state updated
    ↓
GitHub link becomes visible
    ↓
TaskTimer mounts and reads acceptedAt
    ↓
localStorage stores start time
    ↓
Timer starts counting up
```

### Member Dashboard Timer

```
TaskTimer.jsx mounts
    ↓
Check localStorage for task_timer_start_${taskId}
    ↓
If not found:
  → Store current timestamp
  → Use acceptedAt as fallback
    ↓
setInterval updates elapsed time every 1000ms
    ↓
formatTime(elapsed) → HH:MM:SS display
    ↓
Component unmounts → interval cleared
    ↓
Next page load → reads localStorage, timer resumes from correct time
```

### Auth Flow - New User

```
User logs in via Clerk
    ↓
Layout.jsx checks: user exists?
    ↓
fetchWorkspaces() called
    ↓
workspaceController.getUserWorkspaces()
    ↓
Check: workspaces.length > 0?
    ↓
NO → Show role selection screen
    ↓
User clicks "I am an Admin"
    ↓
setShowAdminSetup(true)
    ↓
CreateOrganization displayed
    ↓
Admin creates org via Clerk
    ↓
organization?.id changes
    ↓
Re-fetch workspaces triggered
    ↓
Workspace appears in list
    ↓
App renders main dashboard
    ↓
Admin sees AdminDashboard
```

### Auth Flow - Invited Member

```
User receives invitation email
    ↓
Clicks link, signs up via Clerk
    ↓
workspaceController.addMember() called (from Team page by admin)
    ↓
WorkspaceMember created with MEMBER role
    ↓
Member logs in
    ↓
fetchWorkspaces() called
    ↓
Workspace found in results
    ↓
currentMember = workspace.members.find(...)
    ↓
Check: currentMember.isBlocked?
    ↓
NO → App renders
    ↓
useRole() detects role === "MEMBER"
    ↓
Dashboard renders MemberDashboard
```

### Auth Flow - Blocked Member

```
Admin blocks member on Team page
    ↓
api.put(/api/workspaces/member/:memberId/block)
    ↓
Member.isBlocked = true
    ↓
Member's browser (if logged in) detects block
    ↓
Layout.jsx checks: currentMember.isBlocked?
    ↓
YES → Render "Account Suspended" screen
    ↓
Member sees message and sign out button
    ↓
Can only sign out
```

## Redux State Shape

```javascript
workspaceSlice = {
  workspaces: [
    {
      id: "...",
      name: "...",
      members: [
        {
          id: "...",
          userId: "...",
          role: "ADMIN" | "MEMBER",
          score: 0-100,
          isBlocked: false,
          user: { name, email, image }
        }
      ],
      projects: [
        {
          id: "...",
          tasks: [
            {
              id: "...",
              title: "...",
              status: "TODO" | "IN_PROGRESS" | "DONE",
              isAccepted: false | true,
              acceptedAt: "2026-05-05T...",
              github_url: "https://github.com/...",
              assignee: { ... },
              // ... other fields
            }
          ]
        }
      ]
    }
  ],
  currentWorkspace: { ... } // same structure
}
```

## Key Components Relationship

```
Layout
  ├── Navbar
  ├── Sidebar
  └── Outlet
      ├── Dashboard
      │   ├── AdminDashboard (if isAdmin)
      │   │   ├── StatsGrid
      │   │   ├── ProjectOverview
      │   │   ├── RecentActivity
      │   │   └── TeamPerformancePanel (with ScoreInput, Block buttons)
      │   │
      │   └── MemberDashboard (if !isAdmin)
      │       ├── StatsGrid
      │       ├── GitHubTasksSection
      │       │   └── TaskTimer (for each task)
      │       └── AllMyTasksSection
      │
      ├── Team
      │   └── ScoreInput (for admin)
      │   └── Block/Unblock buttons (for admin)
      │
      └── TaskDetails
          ├── [NEW] Accept Button (if !isAccepted && isAssignee)
          └── [NEW] TaskTimer (if isAccepted)
```

## API Endpoints Summary

### Workspace Endpoints
| Method | Endpoint | Auth | Handler |
|--------|----------|------|---------|
| GET | `/api/workspaces/` | ✅ | getUserWorkspaces |
| POST | `/api/workspaces/add-member` | ✅ | addMember |
| PUT | `/api/workspaces/member/:memberId/block` | ✅ ADMIN | blockMember |
| PUT | `/api/workspaces/member/:memberId/score` | ✅ ADMIN | updateMemberScore |

### Task Endpoints
| Method | Endpoint | Auth | Handler |
|--------|----------|------|---------|
| POST | `/api/tasks/` | ✅ | createTask |
| PUT | `/api/tasks/:id` | ✅ | updateTask |
| PUT | `/api/tasks/:id/accept` | ✅ | acceptTask |
| POST | `/api/tasks/delete` | ✅ | deleteTask |

## Files Changed Summary

### New Files (3)
- `client/src/pages/AdminDashboard.jsx`
- `client/src/pages/MemberDashboard.jsx`
- `client/src/components/TaskTimer.jsx`

### Modified Files (8)
- `server/prisma/schema.prisma` → Added fields
- `server/controllers/workspaceController.js` → Added 2 functions
- `server/controllers/taskController.js` → Added 1 function
- `server/routes/workspaceRoutes.js` → Added 2 routes
- `server/routes/taskRoutes.js` → Added 1 route
- `client/src/pages/Layout.jsx` → Auth flow + blocked screen
- `client/src/pages/Dashboard.jsx` → Role branching
- `client/src/pages/Team.jsx` → Block/score controls
- `client/src/pages/TaskDetails.jsx` → Accept + timer
- `client/src/features/workspaceSlice.js` → updateMember action

**Total: 11 files touched**

---

## Deployment Notes

1. **Database Migration**: Run before deploying
   ```bash
   npx prisma migrate dev --name add_score_blocked_accepted_fields
   ```

2. **Environment Variables**: Already configured
   - DATABASE_URL (Neon)
   - DIRECT_URL (Neon)
   - Clerk keys

3. **Hot Module Replacement**: Working on dev server
   - All files sync automatically
   - Changes visible in real-time

4. **Build Ready**: No TypeScript errors
   - All imports valid
   - All dependencies installed
   - All syntax correct
