# TaskManager 🗂️

A full-stack **project management platform** with dual-role workspaces — Admins manage teams, projects, and tasks while Members track their assignments with live timers and GitHub integration.

![Stack](https://img.shields.io/badge/React-18-blue?logo=react) ![Node](https://img.shields.io/badge/Node.js-Express-green?logo=node.js) ![Prisma](https://img.shields.io/badge/Prisma-ORM-2D3748?logo=prisma) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql) ![Clerk](https://img.shields.io/badge/Auth-Clerk-6C47FF?logo=clerk)

---

## ✨ Features

### 👑 Admin
- Create & manage **Workspaces** (backed by Clerk Organizations)
- Full **Project lifecycle** management — status, priority, dates, progress
- Create **Tasks** with type, priority, due date, assignee, and **GitHub issue URL**
- **Block / Unblock** team members instantly
- Set & edit **Performance Scores** (0–100) per member
- View **Team Performance** panel with per-member completion rates
- Invite members via email

### 👤 Member
- **Personal Dashboard** — see only assigned tasks
- **Accept tasks** → live elapsed timer starts automatically
- **GitHub issue link** surfaces alongside the timer for quick repo access
- **Performance Score** badge displayed on dashboard
- Task calendar & analytics views

### 🔐 Auth & Access
- Clerk-powered authentication (sign-up, sign-in, org creation)
- **Role-based access control** — enforced on both frontend (React) and backend (Express middleware)
- Blocked members see a locked screen on login

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Redux Toolkit, React Router v6 |
| Styling | Vanilla CSS + Tailwind utility classes |
| Auth | Clerk (`@clerk/clerk-react`, `@clerk/express`) |
| Backend | Node.js, Express 5 |
| ORM | Prisma 6 |
| Database | PostgreSQL (Neon serverless) |
| Events | Inngest (async emails, webhook sync) |
| Email | Nodemailer |

---

## 📁 Project Structure

```
project-management-main/
├── client/                   # React frontend (Vite)
│   └── src/
│       ├── app/              # Redux store
│       ├── components/       # Reusable UI components
│       │   ├── CreateProjectDialog.jsx
│       │   ├── CreateTaskDialog.jsx
│       │   ├── InviteMemberDialog.jsx
│       │   ├── ProjectTasks.jsx
│       │   ├── ProjectCalendar.jsx
│       │   ├── ProjectAnalytics.jsx
│       │   ├── TaskTimer.jsx
│       │   └── ...
│       ├── features/         # Redux slices
│       │   └── workspaceSlice.js
│       ├── hooks/            # Custom hooks (useRole)
│       ├── pages/
│       │   ├── Layout.jsx        # Auth guard + workspace gate
│       │   ├── LoginPage.jsx     # Dual-role login UI
│       │   ├── Dashboard.jsx     # Role router → Admin/Member
│       │   ├── AdminDashboard.jsx
│       │   ├── MemberDashboard.jsx
│       │   ├── Projects.jsx
│       │   ├── ProjectDetails.jsx
│       │   ├── TaskDetails.jsx
│       │   └── Team.jsx
│       └── configs/
│           └── api.js            # Axios instance
│
└── server/                   # Node.js + Express backend
    ├── controllers/
    │   ├── workspaceController.js
    │   ├── projectController.js
    │   ├── taskController.js
    │   └── commentController.js
    ├── routes/
    │   ├── workspaceRoutes.js
    │   ├── projectRoutes.js
    │   ├── taskRoutes.js
    │   └── commentRoutes.js
    ├── middlewares/
    │   └── authMiddleware.js     # Clerk JWT verification
    ├── inngest/
    │   └── index.js              # Inngest functions (email, sync)
    ├── configs/
    │   ├── prisma.js
    │   └── nodemailer.js
    ├── prisma/
    │   └── schema.prisma
    └── server.js
```

---

## ⚙️ Local Setup

### Prerequisites
- Node.js 18+
- A [Clerk](https://clerk.com) account (free)
- A [Neon](https://neon.tech) PostgreSQL database (free)

---

### 1. Clone & Install

```bash
git clone https://github.com/jayeshpandey01/task_manager.git
cd task_manager

# Install server deps
cd server && npm install

# Install client deps
cd ../client && npm install
```

---

### 2. Server Environment — `server/.env`

```env
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require&channel_binding=require"
DIRECT_URL="postgresql://user:pass@direct-host/db?sslmode=require&channel_binding=require"

CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."

INNGEST_EVENT_KEY="..."

EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT=587
EMAIL_USER="your_email@gmail.com"
EMAIL_PASS="your_app_password"
```

---

### 3. Client Environment — `client/.env`

```env
VITE_CLERK_PUBLISHABLE_KEY="pk_test_..."
VITE_API_URL="http://localhost:5000"
VITE_BASEURL="http://localhost:5000"
```

---

### 4. Database Migration

```bash
cd server
npx prisma migrate dev --name init
npx prisma generate
```

---

### 5. Run Development Servers

```bash
# Terminal 1 — Backend
cd server
npm run server

# Terminal 2 — Frontend
cd client
npm run dev
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5000`

---

## 🔌 API Routes

### Workspaces — `/api/workspaces`
| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Get user's workspaces |
| `POST` | `/` | Create workspace directly |
| `POST` | `/add-member` | Add member to workspace |
| `PUT` | `/member/:id/block` | Block / unblock member |
| `PUT` | `/member/:id/score` | Update member score |

### Projects — `/api/projects`
| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Create project |
| `PUT` | `/:id` | Update project |
| `DELETE` | `/:id` | Delete project |

### Tasks — `/api/tasks`
| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Create task (with optional GitHub URL) |
| `PUT` | `/:id` | Update task |
| `PUT` | `/:id/accept` | Member accepts task (starts timer) |
| `DELETE` | `/` | Delete tasks |

### Comments — `/api/comments`
| Method | Path | Description |
|---|---|---|
| `GET` | `/:taskId` | Get comments for a task |
| `POST` | `/` | Add comment |

---

## 🗄️ Database Schema (Key Models)

```prisma
model User          { id, name, email, image }
model Workspace     { id, name, slug, ownerId, members[], projects[] }
model WorkspaceMember { userId, workspaceId, role (ADMIN|MEMBER), score, isBlocked }
model Project       { name, description, priority, status, start_date, end_date, tasks[] }
model Task          { title, type, status, priority, assigneeId, due_date,
                      github_url?, isAccepted, acceptedAt? }
model Comment       { content, userId, taskId }
```

---

## 📧 Async Events (Inngest)

| Event | Trigger | Action |
|---|---|---|
| `clerk/user.created` | Clerk webhook | Sync user to DB |
| `clerk/organization.created` | Clerk webhook | Sync workspace to DB |
| `clerk/organizationInvitation.accepted` | Clerk webhook | Add member to workspace |
| `app/task.assigned` | Task creation | Send assignment email + due-date reminder |

> **Note:** Clerk webhooks require a public URL in production. In local dev, workspace and user sync happens via the direct `POST /api/workspaces` endpoint.

---

## 👤 Author

**Jayesh Pandey**  
GitHub: [@jayeshpandey01](https://github.com/jayeshpandey01)

---

## 📄 License

MIT
