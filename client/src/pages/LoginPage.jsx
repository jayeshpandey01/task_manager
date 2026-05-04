import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { SignIn, useUser } from "@clerk/clerk-react";
import { Shield, Users, CheckCircle } from "lucide-react";

const TABS = [
  {
    id: "admin",
    label: "Admin",
    icon: Shield,
    accent: "blue",
    heading: "Admin Login",
    subheading: "Sign in to manage your workspace, projects, and team.",
    badge: "WORKSPACE OWNER",
    badgeColor: "bg-blue-500",
    features: [
      "Create & manage workspaces",
      "Assign tasks to team members",
      "Track performance with scores",
      "Block / unblock members",
    ],
    borderActive: "border-blue-500",
    textActive: "text-blue-600 dark:text-blue-400",
    bgActive: "bg-blue-50 dark:bg-blue-500/10",
    iconBg: "bg-blue-100 dark:bg-blue-500/15",
    dotColor: "bg-blue-500",
  },
  {
    id: "member",
    label: "Member",
    icon: Users,
    accent: "indigo",
    heading: "Member Login",
    subheading: "Sign in to view your tasks, track progress, and collaborate.",
    badge: "TEAM MEMBER",
    badgeColor: "bg-indigo-500",
    features: [
      "View assigned tasks",
      "Accept tasks & start timers",
      "Access GitHub links",
      "Track your performance score",
    ],
    borderActive: "border-indigo-500",
    textActive: "text-indigo-600 dark:text-indigo-400",
    bgActive: "bg-indigo-50 dark:bg-indigo-500/10",
    iconBg: "bg-indigo-100 dark:bg-indigo-500/15",
    dotColor: "bg-indigo-500",
  },
];

const LoginPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isLoaded, isSignedIn } = useUser();

  const roleParam = searchParams.get("role");
  const [activeTab, setActiveTab] = useState(
    roleParam === "member" ? "member" : "admin"
  );

  // If already signed in, redirect to dashboard
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate("/", { replace: true });
    }
  }, [isLoaded, isSignedIn, navigate]);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ role: tabId });
  };

  const tab = TABS.find((t) => t.id === activeTab);
  const TabIcon = tab.icon;

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-zinc-950">
      {/* ── Left panel: branding + feature list ── */}
      <div className="hidden lg:flex lg:w-[420px] xl:w-[480px] flex-col justify-between p-10 bg-white dark:bg-zinc-900 border-r border-gray-100 dark:border-zinc-800 shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">TM</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-base">
            TaskManager
          </span>
        </div>

        {/* Middle content */}
        <div>
          {/* Role indicator */}
          <span
            className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full text-white mb-5 ${tab.badgeColor}`}
          >
            <TabIcon className="size-3" />
            {tab.badge}
          </span>

          <h2 className="text-3xl font-semibold text-gray-900 dark:text-white leading-tight mb-3">
            {activeTab === "admin"
              ? "Manage your team with confidence"
              : "Stay on top of your work"}
          </h2>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mb-8 leading-relaxed">
            {activeTab === "admin"
              ? "TaskManager gives you full control over projects, tasks, and team performance in one place."
              : "See all your assigned tasks, track timers, access GitHub links, and monitor your score — all in one dashboard."}
          </p>

          {/* Feature list */}
          <ul className="space-y-3">
            {tab.features.map((f) => (
              <li key={f} className="flex items-center gap-3">
                <CheckCircle
                  className={`size-4 shrink-0 ${tab.textActive}`}
                />
                <span className="text-sm text-gray-600 dark:text-zinc-300">
                  {f}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Role switch hint */}
        <p className="text-xs text-gray-400 dark:text-zinc-600">
          Logging in as{" "}
          <span className={`font-medium ${tab.textActive}`}>
            {tab.badge}
          </span>
          . Wrong role?{" "}
          <button
            onClick={() =>
              handleTabChange(activeTab === "admin" ? "member" : "admin")
            }
            className="underline hover:text-gray-600 dark:hover:text-zinc-300 transition"
          >
            Switch to {activeTab === "admin" ? "Member" : "Admin"}
          </button>
        </p>
      </div>

      {/* ── Right panel: tab switcher + Clerk SignIn ── */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-[420px]">
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center justify-center gap-2.5 mb-8">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">TM</span>
            </div>
            <span className="font-semibold text-gray-900 dark:text-white text-base">
              TaskManager
            </span>
          </div>

          {/* Tab switcher */}
          <div className="flex items-center gap-2 p-1 rounded-xl bg-gray-100 dark:bg-zinc-800 mb-6">
            {TABS.map((t) => {
              const Icon = t.icon;
              const isActive = t.id === activeTab;
              return (
                <button
                  key={t.id}
                  onClick={() => handleTabChange(t.id)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-white dark:bg-zinc-900 shadow-sm text-gray-900 dark:text-white"
                      : "text-gray-500 dark:text-zinc-400 hover:text-gray-700 dark:hover:text-zinc-200"
                  }`}
                >
                  <Icon className="size-4 shrink-0" />
                  {t.label}
                  {isActive && (
                    <span
                      className={`w-1.5 h-1.5 rounded-full shrink-0 ${t.dotColor}`}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Role description (mobile) */}
          <div
            className={`lg:hidden flex items-start gap-3 p-4 rounded-xl border mb-5 ${tab.bgActive} border-${tab.accent === "blue" ? "blue" : "indigo"}-200 dark:border-${tab.accent === "blue" ? "blue" : "indigo"}-800`}
          >
            <div className={`p-1.5 rounded-lg ${tab.iconBg} shrink-0`}>
              <TabIcon className={`size-4 ${tab.textActive}`} />
            </div>
            <div>
              <p className={`text-xs font-semibold ${tab.textActive} mb-0.5`}>
                {tab.badge}
              </p>
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                {tab.subheading}
              </p>
            </div>
          </div>

          {/* Clerk SignIn — one instance per tab key so it fully remounts */}
          <div key={activeTab} className="flex justify-center">
            <SignIn
              routing="hash"
              afterSignInUrl="/"
              afterSignUpUrl="/"
              appearance={{
                elements: {
                  rootBox: "w-full",
                  card: "shadow-none border border-gray-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 w-full",
                  headerTitle:
                    "text-gray-900 dark:text-white font-semibold text-lg",
                  headerSubtitle: "text-gray-500 dark:text-zinc-400 text-sm",
                  socialButtonsBlockButton:
                    "border border-gray-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white dark:hover:bg-zinc-700",
                  formFieldInput:
                    "border-gray-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white rounded-lg",
                  formButtonPrimary:
                    activeTab === "admin"
                      ? "bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                      : "bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg",
                  footerActionLink:
                    activeTab === "admin"
                      ? "text-blue-600 dark:text-blue-400"
                      : "text-indigo-600 dark:text-indigo-400",
                  dividerLine: "bg-gray-200 dark:bg-zinc-700",
                  dividerText: "text-gray-400 dark:text-zinc-500",
                },
              }}
            />
          </div>

          {/* Note about member invitation */}
          {activeTab === "member" && (
            <p className="mt-4 text-center text-xs text-gray-400 dark:text-zinc-500">
              New member? You need an{" "}
              <span className="font-medium text-indigo-500">
                invitation email
              </span>{" "}
              from your admin before you can access the app.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
