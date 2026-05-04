import { useSelector } from "react-redux";
import { useUser } from "@clerk/clerk-react";

export const useRole = () => {
  const { user } = useUser();
  const currentWorkspace = useSelector(
    (state) => state?.workspace?.currentWorkspace
  );

  if (!user || !currentWorkspace) {
    return { isAdmin: false, isMember: false, role: null };
  }

  const currentMember = currentWorkspace.members?.find(
    (member) => member.userId === user.id
  );

  const role = currentMember?.role || null;

  return {
    isAdmin: role === "ADMIN",
    isMember: role === "MEMBER",
    role,
  };
};
