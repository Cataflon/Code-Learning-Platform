import { AlertTriangle, Check, Clock, Loader2 } from "lucide-react";

import { Chip } from "./ui.jsx";

const STATUS = {
  queued: { label: "Queued", tone: "neutral", icon: Clock },
  running: { label: "Running", tone: "info", icon: Loader2 },
  done: { label: "Done", tone: "pass", icon: Check },
  error: { label: "Error", tone: "fail", icon: AlertTriangle },
};

/** Lifecycle of a submission: queued -> running -> done | error. */
export default function StatusBadge({ status }) {
  const { label, tone, icon } = STATUS[status] ?? STATUS.queued;
  return (
    <Chip tone={tone} icon={icon} className={status === "running" ? "[&>svg]:animate-spin" : ""}>
      {label}
    </Chip>
  );
}
