import prisma from "../configs/prisma.js";

// Get all workspaces for user
export const getUserWorkspaces = async (req, res) => {
  try {
    const { userId } = await req.auth();
    const workspaces = await prisma.workspace.findMany({
      where: {
        members: { some: { userId: userId } },
      },
      include: {
        members: { include: { user: true } },
        projects: {
          include: {
            tasks: {
              include: {
                assignee: true,
                comments: {
                  include: {
                    user: true,
                  },
                },
              },
            },
            members: { include: { user: true } },
          },
        },
        owner: true,
      },
    });

    res.json({ workspaces });
  } catch (error) {
    console.log(error);
    res.status(500).json({ message: error.code || error.message });
  }
};

// Add member to workspace
export const addMember = async (req, res) => {
  try {
    const { userId } = await req.auth();
    const { email, role, workspaceId, message } = req.body;

    // Check if user exists
    const user = await prisma.user.findUnique({ where: { email } });

    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    // Check if no missing parameters
    if (!workspaceId || !role) {
      return res.status(400).json({ message: "Missing required parameters" });
    }

    // Check if role is valid
    if (!["ADMIN", "MEMBER"].includes(role)) {
      return res.status(400).json({ message: "Invalid role" });
    }

    // fetch workspace
    const workspace = await prisma.workspace.findUnique({
      where: { id: workspaceId },
      include: { members: true },
    });

    if (!workspace) {
      return res.status(404).json({ message: "Workspace not found" });
    }

    // Check creator has admin role
    if (
      !workspace.members.find(
        (member) => member.userId === userId && role === "ADMIN"
      )
    ) {
      return res
        .status(401)
        .json({ message: "You do not have admin privileges" });
    }

    // Check if user is already a member
    const existingMember = workspace.members.find(
      (member) => member.userId === user.id
    );

    if (existingMember) {
      return res.status(400).json({ message: "User is already a member" });
    }

    const member = await prisma.workspaceMember.create({
      data: {
        userId: user.id,
        workspaceId,
        role,
        message,
      },
    });

    return res.json({ member, message: "Member added successfully" });
  } catch (error) {
    console.log(error);
    res.status(500).json({ message: error.code || error.message });
  }
};

// Block or unblock a workspace member
export const blockMember = async (req, res) => {
  try {
    const { userId } = await req.auth();
    const { memberId } = req.params;

    const member = await prisma.workspaceMember.findUnique({
      where: { id: memberId },
      include: { workspace: { include: { members: true } } },
    });

    if (!member) {
      return res.status(404).json({ message: "Member not found" });
    }

    // Requester must be ADMIN of this workspace
    const requester = member.workspace.members.find(
      (m) => m.userId === userId
    );

    if (!requester || requester.role !== "ADMIN") {
      return res.status(403).json({ message: "Admin privileges required" });
    }

    // Prevent blocking other admins
    if (member.role === "ADMIN") {
      return res.status(400).json({ message: "Cannot block an admin" });
    }

    const updated = await prisma.workspaceMember.update({
      where: { id: memberId },
      data: { isBlocked: !member.isBlocked },
      include: { user: true },
    });

    return res.json({
      member: updated,
      message: updated.isBlocked ? "Member blocked" : "Member unblocked",
    });
  } catch (error) {
    console.log(error);
    res.status(500).json({ message: error.code || error.message });
  }
};

// Update a member's performance score
export const updateMemberScore = async (req, res) => {
  try {
    const { userId } = await req.auth();
    const { memberId } = req.params;
    const { score } = req.body;

    if (typeof score !== "number" || score < 0 || score > 100) {
      return res
        .status(400)
        .json({ message: "Score must be a number between 0 and 100" });
    }

    const member = await prisma.workspaceMember.findUnique({
      where: { id: memberId },
      include: { workspace: { include: { members: true } } },
    });

    if (!member) {
      return res.status(404).json({ message: "Member not found" });
    }

    const requester = member.workspace.members.find(
      (m) => m.userId === userId
    );

    if (!requester || requester.role !== "ADMIN") {
      return res.status(403).json({ message: "Admin privileges required" });
    }

    const updated = await prisma.workspaceMember.update({
      where: { id: memberId },
      data: { score },
      include: { user: true },
    });

    return res.json({ member: updated, message: "Score updated" });
  } catch (error) {
    console.log(error);
    res.status(500).json({ message: error.code || error.message });
  }
};
