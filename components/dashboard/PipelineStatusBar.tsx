import {analysisStatus} from "@/utils/analysis-presentation";
import type {PipelineStatus} from "@/types/audit";
interface PipelineStatusBarProps {
  status: PipelineStatus | "idle";
  currentNode?: string;
  layer2Status?: "running" | "completed" | "failed";
}
export function PipelineStatusBar({status,layer2Status}:PipelineStatusBarProps) {
  const advanced={running:"En proceso",completed:"Completado",failed:"No se pudo guardar el informe avanzado"};
  return <div className="glass px-5 py-4 text-sm text-zinc-300">
    Estado del análisis: {analysisStatus[status]??"Sin análisis cargado"}
    {layer2Status&&<span className="ml-4">Informe avanzado: {advanced[layer2Status]}</span>}
  </div>;
}
