import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { API_BASE_URL, MODEL_SERVICE_URL } from '../core/api';
import { Governance } from './governance';

/**
 * O console fala com DOIS serviços, e estes testes fixam qual chamada vai para onde:
 * governança e registry no model_service; cálculo de métricas no api_service, porque é
 * quem tem `decisao`/`recompensa`.
 */
describe('Governance', () => {
  let service: Governance;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Governance, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(Governance);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lista políticas no model_service', () => {
    service.policies().subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/policies');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('lê os pesos de uma política', () => {
    service.arms('linucb-v1').subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/policies/linucb-v1/arms');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('promove uma política', () => {
    service.promote('thompson-v1').subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/policies/thompson-v1/promote');
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('lista ciclos de retreino', () => {
    service.cycles().subscribe();
    httpMock.expectOne(MODEL_SERVICE_URL + '/retrain-cycles').flush([]);
  });

  it('abre ciclo enviando as métricas apuradas', () => {
    service.startCycle('linucb-v1', { regret: 0.2 }).subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/retrain-cycles');
    expect(req.request.body).toEqual({
      policy_id: 'linucb-v1',
      run_id: null,
      metrics: { regret: 0.2 },
    });
    req.flush({});
  });

  it('o gate humano leva quem aprovou', () => {
    service.decide('run-1', 'approve', 7, 'ok').subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/approvals?user_id=7');
    expect(req.request.body).toEqual({ run_id: 'run-1', decision: 'approve', note: 'ok' });
    req.flush({});
  });

  it('nota é opcional no gate', () => {
    service.decide('run-1', 'reject', 7).subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/approvals?user_id=7');
    expect(req.request.body.note).toBeNull();
    req.flush({});
  });

  it('rollback aponta a política de destino', () => {
    service.rollback('run-1', 'antiga-v0').subscribe();
    const req = httpMock.expectOne(MODEL_SERVICE_URL + '/retrain-cycles/run-1/rollback');
    expect(req.request.body).toEqual({ to_policy_id: 'antiga-v0' });
    req.flush({});
  });

  it('lista métricas publicadas, com e sem filtro', () => {
    service.publishedMetrics().subscribe();
    httpMock.expectOne(MODEL_SERVICE_URL + '/metrics').flush([]);

    service.publishedMetrics('linucb-v1').subscribe();
    httpMock.expectOne(MODEL_SERVICE_URL + '/metrics?policy_id=linucb-v1').flush([]);
  });

  it('apura métricas no api_service (é lá que estão decisao/recompensa)', () => {
    service.computeMetrics('linucb-v1').subscribe();
    const req = httpMock.expectOne(
      API_BASE_URL + '/monitoring/metrics?policy_version=linucb-v1&window_days=14',
    );
    expect(req.request.method).toBe('GET');
    req.flush({ policyVersion: 'linucb-v1', windowDays: 14, decisions: 0, metrics: [] });
  });

  it('respeita a janela pedida', () => {
    service.computeMetrics('linucb-v1', 30).subscribe();
    httpMock
      .expectOne(API_BASE_URL + '/monitoring/metrics?policy_version=linucb-v1&window_days=30')
      .flush({ policyVersion: 'linucb-v1', windowDays: 30, decisions: 0, metrics: [] });
  });

  it('publica as métricas apuradas', () => {
    service.publishMetrics('linucb-v1').subscribe();
    const req = httpMock.expectOne(
      API_BASE_URL + '/monitoring/metrics/linucb-v1/publish?window_days=14',
    );
    expect(req.request.method).toBe('POST');
    req.flush({ policyVersion: 'linucb-v1', windowDays: 14, decisions: 0, metrics: [] });
  });

  it('lista os modelos do registry', () => {
    service.registryModels().subscribe();
    httpMock.expectOne(MODEL_SERVICE_URL + '/registry/models').flush([]);
  });
});
