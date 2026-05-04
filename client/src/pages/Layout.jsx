import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import { Outlet } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { loadTheme } from "../features/themeSlice";
import { Loader2Icon, ShieldX, Clock, ShieldCheck } from "lucide-react";
import {
  useUser,
  SignIn,
  useAuth,
  CreateOrganization,
  useOrganization,
  useClerk,
} from "@clerk/clerk-react";
import { fetchWorkspaces } from "../features/workspaceSlice";

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showAdminSetup, setShowAdminSetup] = useState(false);
  const { loading, workspaces, currentWorkspace } = useSelector(
    (state) => state.workspace
  );
  const dispatch = useDispatch();

  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const { organization } = useOrganization();
  const { signOut } = useClerk();

  // Initial load of theme
  useEffect(() => {
    dispatch(loadTheme());
  }, []);

  // Fetch workspaces once user is loaded — independent of Clerk org
  useEffect(() => {
    if (isLoaded && user) {
      dispatch(fetchWorkspaces({ getToken }));
    }
  }, [user, isLoaded]);

  // Re-fetch when Clerk org changes (after admin creates org)
  useEffect(() => {
    if (isLoaded && user && organization?.id) {
      dispatch(fetchWorkspaces({ getToken }));
    }
  }, [organization?.id]);

  // Not logged in
  if (!isLoaded || (!user && !loading)) {
    return (
      <div className="flex justify-center items-center h-screen bg-white dark:bg-zinc-950">
        <SignIn />
      </div>
    );
  }

  // Loading workspaces
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-zinc-950">
        <Loader2Icon className="size-7 text-blue-500 animate-spin" />
      </div>
    );
  }

  // User has no workspace yet — show role-selection screen
  if (user && isLoaded && workspaces.length === 0) {
    // Admin chose to set up a workspace
    if (showAdminSetup) {
      return (
        <div className="min-h-screen flex justify-center items-center bg-gray-50 dark:bg-zinc-950 p-4">
          <div className="flex flex-col items-center gap-4 w-full">
            <div className="text-center mb-2">
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                Step 2 of 2 &mdash; Create your workspace
              </p>
              <p className="text-sm text-gray-600 dark:text-zinc-300 mt-1">
                After creating, you will be taken to your Admin dashboard automatically.
              </p>
            </div>
            <CreateOrganization />
            <button
              onClick={() => setShowAdminSetup(false)}
              className="text-sm text-gray-400 dark:text-zinc-500 hover:underline"
            >
              &larr; Back
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 p-4">
        <div className="w-full max-w-lg">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-500/10 mb-4">
              <ShieldCheck className="size-7 text-blue-500" />
            </div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Welcome, {user.firstName || user.emailAddresses?.[0]?.emailAddress?.split("@")[0] || "there"}
            </h1>
            <p className="text-sm text-gray-500 dark:text-zinc-400 mt-2">
              You are not part of any workspace yet. Are you an Admin or a Team Member?
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {/* ── Admin path ── */}
            <button
              onClick={() => setShowAdminSetup(true)}
              className="flex items-start gap-4 p-5 rounded-xl border-2 border-blue-500 bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition text-left w-full"
            >
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-500/20 mt-0.5 shrink-0">
                <ShieldCheck className="size-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-semibold text-gray-900 dark:text-white text-sm">
                    I am an Admin
                  </p>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500 text-white font-medium">
                    CREATE WORKSPACE
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mb-3">
                  Create a new workspace, then invite your team. You will get a full admin dashboard with task assignment, scoring, and team management.
                </p>
                {/* Step-by-step for admin */}
                <ol className="space-y-1">
                  {[
                    "Sign up / log in (you are here)",
                    'Click "I am an Admin" and create your workspace',
                    "You land on the Admin dashboard",
                    'Go to Team page → click "Invite Member" to invite teammates by email',
                    "Teammates accept the invite email and log in as Members",
                  ].map((step, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-gray-500 dark:text-zinc-400">
                      <span className="inline-flex items-center justify-center size-4 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 font-bold shrink-0 mt-0.5 text-[10px]">
                        {i + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            </button>

            {/* ── Member path ── */}
            <div className="flex items-start gap-4 p-5 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-left">
              <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-500/20 mt-0.5 shrink-0">
                <Clock className="size-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-semibold text-gray-900 dark:text-white text-sm">
                    I am a Team Member
                  </p>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-400 text-white font-medium">
                    INVITE REQUIRED
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mb-3">
                  You need an invitation from your admin before you can access the app.
                </p>
                {/* Step-by-step for member */}
                <ol className="space-y-1 mb-4">
                  {[
                    "Ask your admin to invite you from the Team page",
                    "Check your email inbox for the invitation link",
                    "Click the link — it opens the app and joins you to the workspace",
                    "Log in (or sign up if first time) with the same email",
                    'Click "Refresh" below — your Member dashboard will appear',
                  ].map((step, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-gray-500 dark:text-zinc-400">
                      <span className="inline-flex items-center justify-center size-4 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold shrink-0 mt-0.5 text-[10px]">
                        {i + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
                <button
                  onClick={() => dispatch(fetchWorkspaces({ getToken }))}
                  className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-700 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-500/20 transition"
                >
                  <Clock className="size-3" />
                  Refresh — I accepted my invitation
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={() => signOut()}
            className="mt-6 w-full text-xs text-center text-gray-400 dark:text-zinc-500 hover:underline"
          >
            Sign out
          </button>
        </div>
      </div>
    );
  }

  // Determine current member record
  const currentMember = currentWorkspace?.members?.find(
    (m) => m.userId === user?.id
  );

  // Blocked member screen
  if (currentMember?.isBlocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 p-4">
        <div className="text-center max-w-sm">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-500/10 mb-5">
            <ShieldX className="size-8 text-red-500" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Account Suspended
          </h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mb-1">
            Your access to{" "}
            <span className="font-medium text-gray-700 dark:text-zinc-300">
              {currentWorkspace?.name || "this workspace"}
            </span>{" "}
            has been suspended by the administrator.
          </p>
          <p className="text-xs text-gray-400 dark:text-zinc-500 mb-6">
            Contact your admin at{" "}
            {currentWorkspace?.owner?.email || "your organization"} to resolve this.
          </p>
          <button
            onClick={() => signOut()}
            className="px-5 py-2 text-sm rounded-lg bg-red-500 hover:bg-red-600 text-white transition"
          >
            Sign out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex bg-white dark:bg-zinc-950 text-gray-900 dark:text-slate-100">
      <Sidebar
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
      />
      <div className="flex-1 flex flex-col h-screen">
        <Navbar
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
        />
        <div className="flex-1 h-full p-6 xl:p-10 xl:px-16 overflow-y-scroll">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default Layout;
