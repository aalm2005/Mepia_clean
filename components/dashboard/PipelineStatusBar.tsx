interface PipelineStatusBarProps {
  status: "idle" | "running" | "completed" | "partial" | "escalated" | "failed";
  currentNode?: string;
  layer2Status?: "running" | "completed" | "failed";
}

const PIPELINE_NODES = ["S1", "S2", "S3", "S4", "N05"] as const;

function getNodeClass(
  node: string,
  status: PipelineStatusBarProps["status"],
  currentNode?: string
): string {
  if (status === "failed" && node === currentNode) {
    return "text-critical";
  }
  if (node === currentNode && status === "running") {
    return "text-accent border-b-2 border-accent animate-pulse";
  }
  if (status === "completed" || status === "escalated" || status === "partial") {
    // All nodes before currentNode are completed; if no currentNode, all are done
    if (!currentNode) return "text-accent";
    const nodeIndex = PIPELINE_NODES.indexOf(node as (typeof PIPELINE_NODES)[number]);
    const currentIndex = PIPELINE_NODES.indexOf(
      currentNode as (typeof PIPELINE_NODES)[number]
    );
    if (nodeIndex < currentIndex) return "text-accent";
    if (nodeIndex === currentIndex) return "text-accent";
    return "text-muted";
  }
  if (status === "failed") {
    const nodeIndex = PIPELINE_NODES.indexOf(node as (typeof PIPELINE_NODES)[number]);
    const currentIndex = currentNode
      ? PIPELINE_NODES.indexOf(currentNode as (typeof PIPELINE_NODES)[number])
      : -1;
    if (nodeIndex < currentIndex) return "text-accent";
    if (nodeIndex === currentIndex) return "text-critical";
    return "text-muted";
  }
  return "text-muted";
}

function Layer2Node({
  layer2Status,
}: {
  layer2Status: "running" | "completed" | "failed";
}) {
  if (layer2Status === "running") {
    return (
      <span className="flex items-center gap-1 text-amber-400">
        <svg
          className="animate-spin h-3 w-3"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"
          />
        </svg>
        [L2]
      </span>
    );
  }
  if (layer2Status === "completed") {
    return <span className="text-accent">[L2] ✓</span>;
  }
  return <span className="text-critical">[L2]</span>;
}

export function PipelineStatusBar({
  status,
  currentNode,
  layer2Status,
}: PipelineStatusBarProps) {
  const showL2 = status === "escalated" && layer2Status !== undefined;

  return (
    <div className="glass px-5 py-4 flex items-center gap-1 text-sm font-mono">
      {PIPELINE_NODES.map((node, index) => (
        <span key={node} className="flex items-center gap-1">
          <span className={getNodeClass(node, status, currentNode)}>{node}</span>
          {(index < PIPELINE_NODES.length - 1 || showL2) && (
            <span className="text-muted">─</span>
          )}
        </span>
      ))}
      {showL2 && layer2Status && <Layer2Node layer2Status={layer2Status} />}
    </div>
  );
}
