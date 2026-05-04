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
        <div className="min-h-screen flex justify-center items-center bg-white dark:bg-zinc-950">
          <div className="flex flex-col items-center gap-4">
            <CreateOrganization />
            <button
              onClick={() => setShowAdminSetup(false)}
              className="text-sm text-gray-500 dark:text-zinc-400 hover:underline"
            >
              Back
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-500/10 mb-4">
              <ShieldCheck className="size-7 text-blue-500" />
            </div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Welcome, {user.firstName || "there"}
            </h1>
            <p className="text-sm text-gray-500 dark:text-zinc-400 mt-2">
              You are not part of any workspace yet. Choose how to proceed.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {/* Admin path */}
            <button
              onClick={() => setShowAdminSetup(true)}
              className="flex items-start gap-4 p-5 rounded-xl border-2 border-blue-500 bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition text-left"
            >
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-500/20 mt-0.5">
                <ShieldCheck className="size-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white text-sm">
                  I am an Admin
                </p>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                  Create a new workspace and invite your team members.
                </p>
              </div>
            </button>

            {/* Member waiting path */}
            <div className="flex items-start gap-4 p-5 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-left">
              <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-500/20 mt-0.5">
                <Clock className="size-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white text-sm">
                  I am a Member
                </p>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                  Waiting for an admin to invite you. Check your email for an
                  invitation link, then refresh this page.
                </p>
                <button
                  onClick={() => dispatch(fetchWorkspaces({ getToken }))}
                  className="mt-3 text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Refresh
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
          <p className="text-sm text-gray-500 dark:text-zinc-400 mb-6">
            Your account has been suspended by the workspace administrator.
            Please contact your admin for more information.
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
