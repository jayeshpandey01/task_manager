import { useState, useEffect, useRef } from "react";
import { Timer, Github, ExternalLink } from "lucide-react";

/**
 * TaskTimer
 * Starts a running HH:MM:SS timer from the moment the GitHub link
 * became visible (i.e., the task's acceptedAt timestamp).
 *
 * Props:
 *  - taskId    (string)  used as localStorage key
 *  - acceptedAt (string) ISO date string — the anchor point for the timer
 *  - githubUrl  (string) the repo link to display
 */
const TaskTimer = ({ taskId, acceptedAt, githubUrl }) => {
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!taskId || !acceptedAt) return;

    const storageKey = `task_timer_start_${taskId}`;

    // Use stored start time or fall back to acceptedAt
    let startTime = localStorage.getItem(storageKey);
    if (!startTime) {
      startTime = new Date(acceptedAt).getTime();
      localStorage.setItem(storageKey, String(startTime));
    } else {
      startTime = Number(startTime);
    }

    const tick = () => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    };

    tick(); // immediate render
    intervalRef.current = setInterval(tick, 1000);

    return () => clearInterval(intervalRef.current);
  }, [taskId, acceptedAt]);

  const formatTime = (totalSeconds) => {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
  };

  if (!githubUrl || !acceptedAt) return null;

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-3 rounded-xl border border-blue-200 dark:border-blue-500/30 bg-blue-50 dark:bg-blue-500/10">
      {/* GitHub link */}
      <a
        href={githubUrl}
        target="_blank"
        rel="noreferrer"
        className="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-zinc-200 hover:text-blue-600 dark:hover:text-blue-400 transition min-w-0"
      >
        <Github className="size-4 flex-shrink-0" />
        <span className="truncate max-w-xs">
          {githubUrl.replace("https://github.com/", "")}
        </span>
        <ExternalLink className="size-3 flex-shrink-0 opacity-60" />
      </a>

      {/* Timer */}
      <div className="flex items-center gap-1.5 ml-auto flex-shrink-0">
        <Timer className="size-3.5 text-blue-500 animate-pulse" />
        <span className="font-mono text-sm font-semibold text-blue-600 dark:text-blue-400 tabular-nums">
          {formatTime(elapsed)}
        </span>
      </div>
    </div>
  );
};

export default TaskTimer;
