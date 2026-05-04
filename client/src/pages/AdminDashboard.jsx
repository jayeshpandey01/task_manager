import { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useUser, useAuth } from "@clerk/clerk-react";
import {
  Plus,
  FolderOpen,
  CheckCircle,
  Users,
  AlertTriangle,
  ShieldX,
  ShieldCheck,
  Star,
  TrendingUp,
  Activity,
} from "lucide-react";
import toast from "react-hot-toast";
import CreateProjectDialog from "../components/CreateProjectDialog";
import ProjectOverview from "../components/ProjectOverview";
import RecentActivity from "../components/RecentActivity";
import api from "../configs/api";
import { updateMember } from "../features/workspaceSlice";

const ScoreInput = ({ member, onSave }) => {
  const [value, setValue] = useState(member.score ?? 0);
  const [editing, setEditing] = useState(false);

  const handleSave = () => {
    const num = Math.min(100, Math.max(0, Number(value)));
    onSave(member.id, num);
    setEditing(false);
  };

  return editing ? (
    <div className="flex items-center gap-1">
      <input
        type="number"
        min={0}
        max={100}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-16 px-2 py-0.5 text-xs rounded border border-gray-300 dark:border-zinc-700 dark:bg-zinc-800 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
        autoFocus
        onKeyDown={(e) => e.key === "Enter" && handleSave()}
      />
      <button
        onClick={handleSave}
        className="text-xs px-2 py-0.5 bg-blue-500 hover:bg-blue-600 text-white rounded transition"
      >
        Save
      </button>
    </div>
  ) : (
    <button
      onClick={() => setEditing(true)}
      className="flex items-center gap-1 text-xs px-2 py-0.5 rounded border border-gray-200 dark:border-zinc-700 hover:border-blue-400 dark:hover:border-blue-500 text-gray-700 dark:text-zinc-300 transition"
      title="Click to edit score"
    >
      <Star className="size-3 text-amber-400" />
      {value}/100
    </button>
  );
};

const AdminDashboard = () => {
  const { user } = useUser();
  const { getToken } = useAuth();
  const dispatch = useDispatch();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [blockingId, setBlockingId] = useState(null);

  const currentWorkspace = useSelector(
    (state) => state?.workspace?.currentWorkspace || null
  );

  const projects = currentWorkspace?.projects || [];
  const members = currentWorkspace?.members || [];

  // Stats
  const totalProjects = projects.length;
  const activeProjects = projects.filter(
    (p) => p.status !== "CANCELLED" && p.status !== "COMPLETED"
  ).length;
  const totalTasks = projects.reduce((a, p) => a + p.tasks.length, 0);
  const overdueTasks = projects.reduce(
    (a, p) =>
      a + p.tasks.filter((t) => new Date(t.due_date) < new Date() && t.status !== "DONE").length,
    0
  );
  const teamMembers = members.filter((m) => m.role === "MEMBER").length;
  const doneTasks = projects.reduce(
    (a, p) => a + p.tasks.filter((t) => t.status === "DONE").length,
    0
  );

  const statCards = [
    {
      icon: FolderOpen,
      title: "Total Projects",
      value: totalProjects,
      sub: `${activeProjects} active`,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      icon: CheckCircle,
      title: "Tasks Done",
      value: doneTasks,
      sub: `of ${totalTasks} total`,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      icon: Users,
      title: "Team Members",
      value: teamMembers,
      sub: "active members",
      color: "text-indigo-500",
      bg: "bg-indigo-500/10",
    },
    {
      icon: AlertTriangle,
      title: "Overdue",
      value: overdueTasks,
      sub: "need attention",
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
  ];

  const handleBlock = async (memberId) => {
    setBlockingId(memberId);
    try {
      const token = await getToken();
      const { data } = await api.put(
        `/api/workspaces/member/${memberId}/block`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      dispatch(updateMember(data.member));
      toast.success(data.message);
    } catch (error) {
      toast.error(error?.response?.data?.message || error.message);
    } finally {
      setBlockingId(null);
    }
  };

  const handleScoreSave = async (memberId, score) => {
    try {
      const token = await getToken();
      const { data } = await api.put(
        `/api/workspaces/member/${memberId}/score`,
        { score },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      dispatch(updateMember(data.member));
      toast.success("Score updated");
    } catch (error) {
      toast.error(error?.response?.data?.message || error.message);
    }
  };

  // Per-member task stats
  const getMemberStats = (userId) => {
    const allTasks = projects.flatMap((p) => p.tasks);
    const assigned = allTasks.filter((t) => t.assignee?.id === userId);
    const done = assigned.filter((t) => t.status === "DONE").length;
    const inProgress = assigned.filter((t) => t.status === "IN_PROGRESS").length;
    const overdue = assigned.filter(
      (t) => new Date(t.due_date) < new Date() && t.status !== "DONE"
    ).length;
    return { total: assigned.length, done, inProgress, overdue };
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-white mb-1">
            Admin Dashboard
          </h1>
          <p className="text-gray-500 dark:text-zinc-400 text-sm">
            Welcome back, {user?.fullName || "Admin"} — {currentWorkspace?.name}
          </p>
        </div>
        <button
          onClick={() => setIsDialogOpen(true)}
          className="flex items-center gap-2 px-5 py-2 text-sm rounded bg-blue-500 hover:bg-blue-600 text-white transition"
        >
          <Plus size={15} />
          New Project
        </button>
        <CreateProjectDialog
          isDialogOpen={isDialogOpen}
          setIsDialogOpen={setIsDialogOpen}
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ icon: Icon, title, value, sub, color, bg }, i) => (
          <div
            key={i}
            className="border border-gray-200 dark:border-zinc-800 rounded-xl p-5 bg-white dark:bg-zinc-900"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">{title}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
                <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1">{sub}</p>
              </div>
              <div className={`p-3 rounded-xl ${bg}`}>
                <Icon size={18} className={color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <ProjectOverview />
          <RecentActivity />
        </div>

        {/* Team Performance Panel */}
        <div className="border border-gray-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-100 dark:border-zinc-800">
            <TrendingUp className="size-4 text-blue-500" />
            <h2 className="font-semibold text-gray-900 dark:text-white text-sm">
              Team Performance
            </h2>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-zinc-800">
            {members
              .filter((m) => m.role === "MEMBER")
              .map((member) => {
                const stats = getMemberStats(member.userId);
                const completion =
                  stats.total > 0
                    ? Math.round((stats.done / stats.total) * 100)
                    : 0;

                return (
                  <div key={member.id} className="px-5 py-4">
                    {/* Member header */}
                    <div className="flex items-center gap-3 mb-3">
                      <img
                        src={member.user?.image}
                        alt={member.user?.name}
                        className="size-8 rounded-full bg-gray-200 dark:bg-zinc-800 flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {member.user?.name || "Member"}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-zinc-500 truncate">
                          {member.user?.email}
                        </p>
                      </div>
                      {member.isBlocked && (
                        <span className="text-xs px-1.5 py-0.5 bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 rounded">
                          Blocked
                        </span>
                      )}
                    </div>

                    {/* Task bar */}
                    <div className="mb-2">
                      <div className="flex justify-between text-xs text-gray-400 dark:text-zinc-500 mb-1">
                        <span>Completion</span>
                        <span>{completion}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-gray-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all"
                          style={{ width: `${completion}%` }}
                        />
                      </div>
                    </div>

                    {/* Mini stats */}
                    <div className="flex gap-3 text-xs text-gray-500 dark:text-zinc-400 mb-3">
                      <span className="flex items-center gap-1">
                        <Activity className="size-3 text-blue-400" />
                        {stats.inProgress} in progress
                      </span>
                      <span className="flex items-center gap-1">
                        <AlertTriangle className="size-3 text-amber-400" />
                        {stats.overdue} overdue
                      </span>
                    </div>

                    {/* Controls */}
                    <div className="flex items-center justify-between gap-2">
                      <ScoreInput member={member} onSave={handleScoreSave} />
                      <button
                        onClick={() => handleBlock(member.id)}
                        disabled={blockingId === member.id}
                        className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded border transition ${
                          member.isBlocked
                            ? "border-emerald-300 dark:border-emerald-700 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10"
                            : "border-red-200 dark:border-red-800 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10"
                        } disabled:opacity-50`}
                      >
                        {member.isBlocked ? (
                          <>
                            <ShieldCheck className="size-3" />
                            Unblock
                          </>
                        ) : (
                          <>
                            <ShieldX className="size-3" />
                            Block
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}

            {members.filter((m) => m.role === "MEMBER").length === 0 && (
              <div className="px-5 py-8 text-center">
                <Users className="size-8 text-gray-300 dark:text-zinc-600 mx-auto mb-2" />
                <p className="text-xs text-gray-400 dark:text-zinc-500">
                  No team members yet. Invite some from the Team page.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
