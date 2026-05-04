import express from "express";
import {
  addMember,
  getUserWorkspaces,
  blockMember,
  updateMemberScore,
} from "../controllers/workspaceController.js";

const workspaceRouter = express.Router();

workspaceRouter.get("/", getUserWorkspaces);
workspaceRouter.post("/add-member", addMember);
workspaceRouter.put("/member/:memberId/block", blockMember);
workspaceRouter.put("/member/:memberId/score", updateMemberScore);

export default workspaceRouter;
