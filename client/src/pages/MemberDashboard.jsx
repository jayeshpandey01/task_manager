import { useSelector, useDispatch } from "react-redux";
import { useUser, useAuth } from "@clerk/clerk-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  ListTodo,
  CheckCheck,
  Star,
  Github,
  ChevronRight,
} from "lucide-react";
import toast from "react-hot-toast";
import api from "../configs/api";
import { updateTask } from "../features/workspaceSlice";
import TaskTimer from "../components/TaskTimer";

const statusColors = {
  DONE: "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400",
  IN_PROGRESS:
    "bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400",
  TODO: "bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-zinc-300",
};

const priorityColors = {
  HIGH: "text-red-500",
  MEDIUM: "text-amber-500",
  LOW: "text-emerald-500",
};

const MemberDashboard = () => {
  const { user } = useUser();
  const { getToken } = useAuth();
  const dispatch = useDispatch();
  const [acceptingId, setAcceptingId] = useState(null);

  const currentWorkspace = useSelector(
    (state) => state?.workspace?.currentWorkspace || null
  );

  const projects = currentWorkspace?.projects || [];
  const allTasks = projects.flatMap((p) => p.tasks);
  const myTasks = allTasks.filter((t) => t.assignee?.id === user?.id);

  // Stats
  const totalTasks = myTasks.length;
  const doneTasks = myTasks.filter((t) => t.status === "DONE").length;
  const inProgressTasks = myTasks.filter(
    (t) => t.status === "IN_PROGRESS"
  ).length;
  const overdueTasks = myTasks.filter(
    (t) => new Date(t.due_date) < new Date() && t.status !== "DONE"
  ).length;

  // Member record (for score display)
  const memberRecord = currentWorkspace?.members?.find(
    (m) => m.userId === user?.id
  );

  // Tasks with GitHub link (only accepted ones)
  const githubTasks = myTasks.filter((t) => t.github_url && t.isAccepted);

  // Pending tasks (not accepted)
  const pendingTasks = myTasks.filter((t) => !t.isAccepted);

  const handleAccept = async (taskId) => {
    setAcceptingId(taskId);
    try {
      const token = await getToken();
      const { data } = await api.put(
        `/api/tasks/${taskId}/accept`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      dispatch(updateTask(data.task));
      toast.success("Task accepted! Timer started.");
    } catch (error) {
      toast.error(error?.response?.data?.message || error.message);
    } finally {
      setAcceptingId(null);
    }
  };

  const statCards = [
    {
      icon: ListTodo,
      label: "Total Tasks",
      value: totalTasks,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      icon: CheckCheck,
      label: "Completed",
      value: doneTasks,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      icon: Clock,
      label: "In Progress",
      value: inProgressTasks,
      color: "text-indigo-500",
      bg: "bg-indigo-500/10",
    },
    {
      icon: AlertTriangle,
      label: "Overdue",
      value: overdueTasks,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-white mb-1">
            My Dashboard
          </h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            Welcome back, {user?.fullName || "Member"} —{" "}
            {currentWorkspace?.name}
          </p>
        </div>

        {memberRecord && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10">
            <Star className="size-4 text-amber-500" />
            <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
              Performance Score: {memberRecord.score ?? 0}/100
            </span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ icon: Icon, label, value, color, bg }, i) => (
          <div
            key={i}
            className="border border-gray-200 dark:border-zinc-800 rounded-xl p-5 bg-white dark:bg-zinc-900"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">{label}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
              </div>
              <div className={`p-3 rounded-xl ${bg}`}>
                <Icon size={18} className={color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Active GitHub Tasks (with timer) */}
      {githubTasks.length > 0 && (
        <div className="border border-gray-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-100 dark:border-zinc-800">
            <Github className="size-4 text-gray-600 dark:text-zinc-300" />
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
              Active Tasks with Repository
            </h2>
          </div>
          <div className="p-5 space-y-3">
            {githubTasks.map((task) => (
              <div
                key={task.id}
                className="rounded-xl border border-gray-100 dark:border-zinc-800 p-4 space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {task.title}
                    </p>
                    <p className={`text-xs mt-0.5 ${priorityColors[task.priority]}`}>
                      {task.priority} priority
                    </p>
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-md flex-shrink-0 ${
                      statusColors[task.status]
                    }`}
                  >
                    {task.status.replace("_", " ")}
                  </span>
                </div>
                <TaskTimer
                  taskId={task.id}
                  acceptedAt={task.acceptedAt}
                  githubUrl={task.github_url}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All My Tasks */}
      <div className="border border-gray-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-100 dark:border-zinc-800">
          <ListTodo className="size-4 text-blue-500" />
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
            All My Tasks
          </h2>
          <span className="ml-auto text-xs px-2 py-0.5 bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400 rounded">
            {myTasks.length}
          </span>
        </div>

        {myTasks.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <CheckCircle2 className="size-10 text-gray-200 dark:text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-gray-400 dark:text-zinc-500">
              No tasks assigned yet.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-zinc-800">
            {myTasks.map((task) => {
              const isOverdue =
                new Date(task.due_date) < new Date() &&
                task.status !== "DONE";

              return (
                <div
                  key={task.id}
                  className="px-5 py-4 flex items-center gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {task.title}
                      </p>
                      {!task.isAccepted && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400">
                          Pending acceptance
                        </span>
                      )}
                      {task.github_url && task.isAccepted && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-400 flex items-center gap-1">
                          <Github className="size-2.5" />
                          Repo linked
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-zinc-500">
                      <span className={isOverdue ? "text-red-500 font-medium" : ""}>
                        Due{" "}
                        {new Date(task.due_date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                        {isOverdue && " (overdue)"}
                      </span>
                      <span className={priorityColors[task.priority]}>
                        {task.priority}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-md ${
                        statusColors[task.status]
                      }`}
                    >
                      {task.status.replace("_", " ")}
                    </span>

                    {/* Accept button if not accepted */}
                    {!task.isAccepted && (
                      <button
                        onClick={() => handleAccept(task.id)}
                        disabled={acceptingId === task.id}
                        className="text-xs px-3 py-1 rounded-lg bg-blue-500 hover:bg-blue-600 text-white transition disabled:opacity-50"
                      >
                        {acceptingId === task.id ? "..." : "Accept"}
                      </button>
                    )}

                    <Link
                      to={`/taskDetails?projectId=${task.projectId}&taskId=${task.id}`}
                      className="p-1 rounded hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-400 dark:text-zinc-500 transition"
                    >
                      <ChevronRight className="size-4" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default MemberDashboard;
