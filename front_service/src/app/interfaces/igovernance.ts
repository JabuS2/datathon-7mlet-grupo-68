/** Contratos de governança — servidos pelo `model_service` (snake_case, pydantic puro). */

export type StatusPolitica = 'shadow' | 'active' | 'retired';
export type StatusCiclo = 'candidate' | 'approved' | 'rejected' | 'promoted' | 'rolled_back';

export interface IPolitica {
  policy_id: string;
  version: string;
  algorithm: string;
  hyperparams: Record<string, unknown>;
  status: StatusPolitica;
  created_at: string;
}

/** Pesos por braço, projetados do estado no Redis — `params` varia por algoritmo. */
export interface IArmState {
  arm_id: string;
  algorithm: string | null;
  params: Record<string, number | string | null>;
}

export interface ICicloRetreino {
  run_id: string;
  policy_id: string;
  status: StatusCiclo;
  metrics: Record<string, number>;
  registry_version: string | null;
  created_at: string;
}

export interface IMetricaPublicada {
  id: number;
  policy_id: string;
  metric: string;
  value: number;
  alert: boolean;
  created_at: string;
}

/** Modelo registrado no MLflow. */
export interface IModeloRegistrado {
  name: string;
  versions: number[];
  latest_version: number;
}

/** Apuração do api_service (é quem tem `decisao`/`recompensa`). */
export interface IMetricsReport {
  policyVersion: string;
  windowDays: number;
  decisions: number;
  metrics: { name: string; value: number; alert: boolean }[];
}
