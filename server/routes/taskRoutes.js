import express from "express";
import {
  createTask,
  deleteTask,
  updateTask,
  acceptTask,
} from "../controllers/taskController.js";

const taskRouter = express.Router();

taskRouter.post("/", createTask);
taskRouter.put("/:id/accept", acceptTask);
taskRouter.put("/:id", updateTask);
taskRouter.post("/delete", deleteTask);

export default taskRouter;
