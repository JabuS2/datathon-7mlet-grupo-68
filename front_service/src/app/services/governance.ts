import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL, MODEL_SERVICE_URL } from '../core/api';
import {
  IArmState,
  ICicloRetreino,
  IMetricaPublicada,
  IMetricsReport,
  IModeloRegistrado,
  IPolitica,
} from '../interfaces/igovernance';

/**
 * Console de operação do modelo.
 *
 * Fala com **dois** serviços, e a divisão não é arbitrária:
 * - `model_service` é dono do ciclo de vida das políticas e do registry;
 * - `api_service` é quem calcula as métricas, porque é quem tem `decisao`/`recompensa`.
 *
 * Atenção: as rotas de governança do model_service não têm autenticação própria hoje — o
 * serviço é interno à rede do compose. Expor essa porta exigiria auth lá.
 */
@Service()
export class Governance {
  private http = inject(HttpClient);

  // ── políticas ──────────────────────────────────────────────
  policies(): Observable<IPolitica[]> {
    return this.http.get<IPolitica[]>(`${MODEL_SERVICE_URL}/policies`);
  }

  arms(policyId: string): Observable<IArmState[]> {
    return this.http.get<IArmState[]>(`${MODEL_SERVICE_URL}/policies/${policyId}/arms`);
  }

  promote(policyId: string): Observable<IPolitica> {
    return this.http.post<IPolitica>(`${MODEL_SERVICE_URL}/policies/${policyId}/promote`, {});
  }

  // ── ciclos de retreino ─────────────────────────────────────
  cycles(): Observable<ICicloRetreino[]> {
    return this.http.get<ICicloRetreino[]>(`${MODEL_SERVICE_URL}/retrain-cycles`);
  }

  /** Abre um ciclo; o model_service versiona o estado no MLflow e grava a versão. */
  startCycle(policyId: string, metrics: Record<string, number>): Observable<ICicloRetreino> {
    return this.http.post<ICicloRetreino>(`${MODEL_SERVICE_URL}/retrain-cycles`, {
      policy_id: policyId,
      run_id: null,
      metrics,
    });
  }

  /** Gate humano: `approve` promove a candidata; `reject` só registra. */
  decide(runId: string, decision: 'approve' | 'reject', userId: number, note?: string) {
    return this.http.post(
      `${MODEL_SERVICE_URL}/approvals?user_id=${userId}`,
      { run_id: runId, decision, note: note ?? null },
    );
  }

  rollback(runId: string, toPolicyId: string): Observable<ICicloRetreino> {
    return this.http.post<ICicloRetreino>(
      `${MODEL_SERVICE_URL}/retrain-cycles/${runId}/rollback`,
      { to_policy_id: toPolicyId },
    );
  }

  // ── métricas ───────────────────────────────────────────────
  /** Publicadas (histórico exibido ao lado da política). */
  publishedMetrics(policyId?: string): Observable<IMetricaPublicada[]> {
    const q = policyId ? `?policy_id=${policyId}` : '';
    return this.http.get<IMetricaPublicada[]>(`${MODEL_SERVICE_URL}/metrics${q}`);
  }

  /** Apuradas agora pelo api_service, a partir do log auditável. */
  computeMetrics(policyVersion: string, windowDays = 14): Observable<IMetricsReport> {
    return this.http.get<IMetricsReport>(
      `${API_BASE_URL}/monitoring/metrics?policy_version=${policyVersion}&window_days=${windowDays}`,
    );
  }

  publishMetrics(policyVersion: string, windowDays = 14): Observable<IMetricsReport> {
    return this.http.post<IMetricsReport>(
      `${API_BASE_URL}/monitoring/metrics/${policyVersion}/publish?window_days=${windowDays}`,
      {},
    );
  }

  // ── registry ───────────────────────────────────────────────
  registryModels(): Observable<IModeloRegistrado[]> {
    return this.http.get<IModeloRegistrado[]>(`${MODEL_SERVICE_URL}/registry/models`);
  }
}
