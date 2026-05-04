import { useRole } from "../hooks/useRole";
import AdminDashboard from "./AdminDashboard";
import MemberDashboard from "./MemberDashboard";

const Dashboard = () => {
  const { isAdmin } = useRole();

  if (isAdmin) return <AdminDashboard />;
  return <MemberDashboard />;
};

export default Dashboard;
