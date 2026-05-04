import { useState, useEffect, useCallback } from "react";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import { Outlet, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { loadTheme } from "../features/themeSlice";
import { Loader2Icon, ShieldX, Clock, ShieldCheck } from "lucide-react";
import {
  useUser,
  useAuth,
  CreateOrganization,
  useOrganization,
  useClerk,
} from "@clerk/clerk-react";
import { fetchWorkspaces } from "../features/workspaceSlice";
import api from "../configs/api";
import toast from "react-hot-toast";

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showAdminSetup, setShowAdminSetup] = useState(false);
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);

  const { loading, workspaces, currentWorkspace } = useSelector(
    (state) => state.workspace
  );
  const dispatch = useDispatch();

  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const { organization } = useOrganization();
  const { signOut } = useClerk();
  const navigate = useNavigate();

  // Initial load of theme
  useEffect(() => {
    dispatch(loadTheme());
  }, []);

  // Fetch workspaces once user is loaded
  useEffect(() => {
    if (isLoaded && user) {
      dispatch(fetchWorkspaces({ getToken }));
    }
  }, [user, isLoaded]);

  // Called once the Clerk org object is available after CreateOrganization completes.
  // Instead of waiting for the Inngest webhook (which requires a public URL),
  // we directly POST to our backend to persist the workspace immediately.
  const handleOrgCreated = useCallback(async () => {
    if (!organization) return;
    setCreatingWorkspace(true);
    try {
      const token = await getToken();
      await api.post(
        "/api/workspaces",
        {
          id: organization.id,
          name: organization.name,
          slug: organization.slug,
          image_url: organization.imageUrl || "",
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Re-fetch so Redux state is fully populated (includes members / projects)
      await dispatch(fetchWorkspaces({ getToken }));
      setShowAdminSetup(false);
    } catch (err) {
      console.error("createWorkspace error:", err);
      const msg =
        err?.response?.data?.message ||
        err?.message ||
        "Failed to create workspace";
      toast.error(msg);
    } finally {
      setCreatingWorkspace(false);
    }
  }, [organization, getToken, dispatch]);

  // Fire once the Clerk org object appears after CreateOrganization completes.
  // We use a ref to guard against double-fires (React Strict Mode).
  useEffect(() => {
    if (organization?.id) {
      handleOrgCreated();
    }
  }, [organization?.id]);

  // Redirect unauthenticated users to login page
  useEffect(() => {
    if (isLoaded && !user) {
      navigate("/login", { replace: true });
    }
  }, [isLoaded, user, navigate]);

  // Not loaded yet, or not logged in — show spinner while redirecting
  if (!isLoaded || !user) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-zinc-950">
        <Loader2Icon className="size-7 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Loading workspaces or actively creating one
  if (loading || creatingWorkspace) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-zinc-950 gap-4">
        <Loader2Icon className="size-8 text-blue-500 animate-spin" />
        <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">
          {creatingWorkspace ? "Setting up your workspace\u2026" : "Loading\u2026"}
        </p>
        {creatingWorkspace && (
          <p className="text-xs text-gray-400 dark:text-zinc-500">
            This usually takes a few seconds.
          </p>
        )}
      </div>
    );
  }

  // User is logged in but has no workspace yet
  if (user && isLoaded && workspaces.length === 0) {
    // Show the Clerk CreateOrganization widget when admin clicks "I am an Admin"
    if (showAdminSetup) {
      return (
        <div className="min-h-screen flex flex-col justify-center items-center bg-gray-50 dark:bg-zinc-950 gap-5 p-4">
          <div className="text-center">
            <p className="text-xs font-medium text-blue-500 uppercase tracking-wide mb-1">
              Create Workspace
            </p>
            <p className="text-sm text-gray-500 dark:text-zinc-400">
              You will be taken to the Admin dashboard once your workspace is ready.
            </p>
          </div>
          <CreateOrganization />
          <button
            onClick={() => setShowAdminSetup(false)}
            className="text-xs text-gray-400 dark:text-zinc-500 hover:underline"
          >
            &larr; Back
          </button>
        </div>
      );
    }

    // Role picker — shown after login when user has no workspace
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 p-4">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2.5 mb-8">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">TM</span>
            </div>
            <span className="font-semibold text-gray-900 dark:text-white">TaskManager</span>
          </div>

          <h1 className="text-xl font-semibold text-gray-900 dark:text-white text-center mb-1">
            One more step
          </h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400 text-center mb-6">
            You are logged in as{" "}
            <span className="font-medium text-gray-700 dark:text-zinc-200">
              {user.primaryEmailAddress?.emailAddress}
            </span>
            . Choose your role to continue.
          </p>

          <div className="space-y-3">
            {/* Admin card */}
            <button
              onClick={() => setShowAdminSetup(true)}
              className="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-blue-500 bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition text-left"
            >
              <div className="p-2.5 rounded-lg bg-blue-100 dark:bg-blue-500/20 shrink-0">
                <ShieldCheck className="size-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="font-semibold text-sm text-gray-900 dark:text-white">
                  I am an Admin
                </p>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">
                  Create a workspace and manage your team
                </p>
              </div>
            </button>

            {/* Member card */}
            <div className="w-full flex items-start gap-4 p-4 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
              <div className="p-2.5 rounded-lg bg-amber-100 dark:bg-amber-500/20 shrink-0 mt-0.5">
                <Clock className="size-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-gray-900 dark:text-white">
                  I am a Member
                </p>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5 mb-3">
                  Check your email for an invitation link from your admin, accept it, then click Refresh.
                </p>
                <button
                  onClick={() => dispatch(fetchWorkspaces({ getToken }))}
                  className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-500/20 transition"
                >
                  <Clock className="size-3" />
                  Refresh after accepting invite
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={() => signOut({ redirectUrl: "/login" })}
            className="mt-6 w-full text-xs text-center text-gray-400 dark:text-zinc-500 hover:underline"
          >
            Sign out and use a different account
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
