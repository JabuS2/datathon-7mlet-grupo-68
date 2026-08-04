import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Account } from '../../services/account';
import { Governance } from '../../services/governance';
import { Admin } from './admin';

describe('Admin', () => {
  let component: Admin;
  let fixture: ComponentFixture<Admin>;

  const politicas = [
    { policy_id: 'linucb-v1', version: '1.0.0', algorithm: 'linucb', hyperparams: {}, status: 'active', created_at: '' },
    { policy_id: 'thompson-v1', version: '1.0.0', algorithm: 'thompson', hyperparams: {}, status: 'shadow', created_at: '' },
    { policy_id: 'antiga-v0', version: '0.9', algorithm: 'linucb', hyperparams: {}, status: 'retired', created_at: '' },
  ];

  const ciclos = [
    { run_id: 'run-1', policy_id: 'thompson-v1', status: 'candidate', metrics: { regret: 0.1 }, registry_version: '3', created_at: '' },
  ];

  const relatorio = {
    policyVersion: 'linucb-v1',
    windowDays: 14,
    decisions: 3,
    metrics: [{ name: 'regret', value: 0.2, alert: false }],
  };

  const governanceMock = {
    policies: vi.fn().mockReturnValue(of(politicas)),
    cycles: vi.fn().mockReturnValue(of(ciclos)),
    publishedMetrics: vi.fn().mockReturnValue(of([])),
    registryModels: vi.fn().mockReturnValue(of([{ name: 'linucb-v1', versions: [1, 2], latest_version: 2 }])),
    arms: vi.fn().mockReturnValue(of([{ arm_id: 'OFF-CR-001', algorithm: 'linucb', params: { b_norm: 1.2 } }])),
    promote: vi.fn().mockReturnValue(of(politicas[1])),
    decide: vi.fn().mockReturnValue(of({})),
    rollback: vi.fn().mockReturnValue(of(ciclos[0])),
    computeMetrics: vi.fn().mockReturnValue(of(relatorio)),
    publishMetrics: vi.fn().mockReturnValue(of(relatorio)),
    startCycle: vi.fn().mockReturnValue(of({ ...ciclos[0], run_id: 'run-2' })),
  };

  const accountMock = {
    me: vi.fn().mockReturnValue(
      of({ id: 7, email: 'op@x.com', tipo: 'operador', codCliente: null, saldoFicticio: null }),
    ),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [Admin],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Governance, useValue: governanceMock },
        { provide: Account, useValue: accountMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Admin);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('deve ser criado e carregar o estado da governança', () => {
    expect(component).toBeTruthy();
    expect(component.politicas()).toHaveLength(3);
    expect(component.ciclos()).toHaveLength(1);
  });

  it('identifica a política ativa e as candidatas pendentes', () => {
    expect(component.ativa()?.policy_id).toBe('linucb-v1');
    expect(component.candidatos()).toHaveLength(1);
  });

  it('carrega o registry só ao abrir a aba MLflow', () => {
    expect(governanceMock.registryModels).not.toHaveBeenCalled();

    component.trocarAba('mlflow');

    expect(governanceMock.registryModels).toHaveBeenCalledOnce();
    expect(component.modelos()).toHaveLength(1);
  });

  it('alterna a lista de pesos da política', () => {
    component.verBracos('linucb-v1');
    expect(component.politicaAberta()).toBe('linucb-v1');
    expect(component.bracos()).toHaveLength(1);

    component.verBracos('linucb-v1');
    expect(component.politicaAberta()).toBeNull();
  });

  it('formata os parâmetros do braço (variam por algoritmo)', () => {
    const texto = component.paramsDe({
      arm_id: 'X',
      algorithm: 'linucb',
      params: { b_norm: 1.2 },
    });
    expect(texto).toContain('b_norm: 1.2');
  });

  it('abrir ciclo apura, publica e anexa as métricas ao ciclo', () => {
    component.abrirCiclo('thompson-v1');

    expect(governanceMock.publishMetrics).toHaveBeenCalledWith('thompson-v1');
    expect(governanceMock.startCycle).toHaveBeenCalledWith('thompson-v1', { regret: 0.2 });
  });

  it('o gate humano registra quem aprovou', () => {
    component.decidir('run-1', 'approve');
    expect(governanceMock.decide).toHaveBeenCalledWith('run-1', 'approve', 7);
  });

  it('não decide sem identificação do operador', () => {
    component.operadorId.set(null);
    component.decidir('run-1', 'approve');
    expect(governanceMock.decide).not.toHaveBeenCalled();
  });

  it('rollback volta para uma política aposentada', () => {
    component.reverter('run-1');
    expect(governanceMock.rollback).toHaveBeenCalledWith('run-1', 'antiga-v0');
  });

  it('não reverte quando não há política aposentada', () => {
    component.politicas.set(politicas.filter((p) => p.status !== 'retired') as never);
    component.reverter('run-1');
    expect(governanceMock.rollback).not.toHaveBeenCalled();
  });

  it('falha na apuração não derruba a tela', () => {
    governanceMock.computeMetrics.mockReturnValueOnce(throwError(() => new Error('403')));
    component.apurar('linucb-v1');
    expect(component.apuracao()).toBeNull();
  });

  // ── renderização das abas ──────────────────────────────────
  // O template é a maior parte do console; sem renderizar cada aba, os ramos de exibição
  // (badges de status, tabelas, estados vazios) nunca são exercitados.

  it('renderiza a aba de políticas com status e ação', () => {
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Operação do modelo');
    expect(texto).toContain('linucb-v1');
    expect(texto).toContain('active');
    expect(texto).toContain('shadow');
    // a ativa não oferece "Promover"
    expect(texto).toContain('Promover');
  });

  it('renderiza a tabela de pesos ao expandir', () => {
    component.verBracos('linucb-v1');
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('OFF-CR-001');
    expect(texto).toContain('b_norm');
    expect(texto).toContain('Ocultar pesos');
  });

  it('renderiza a apuração com o n de decisões', () => {
    component.apurar('linucb-v1');
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Apuração');
    expect(texto).toContain('3 decisões');
    expect(texto).toContain('regret');
  });

  it('avisa quando a apuração não tem decisões no período', () => {
    governanceMock.computeMetrics.mockReturnValueOnce(
      of({ policyVersion: 'linucb-v1', windowDays: 14, decisions: 0, metrics: [] }),
    );
    component.apurar('linucb-v1');
    fixture.detectChanges();

    // zero por ausência de dado não é zero de performance
    expect(fixture.nativeElement.textContent).toContain('ausência de dado');
  });

  it('renderiza a aba de ciclos com o gate pendente', () => {
    component.trocarAba('ciclos');
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('run-1');
    expect(texto).toContain('candidate');
    expect(texto).toContain('Aprovar e promover');
    expect(texto).toContain('aguardando o gate humano');
    expect(texto).toContain('modelo v3 no MLflow');
  });

  it('renderiza a aba de métricas vazia com instrução', () => {
    component.trocarAba('metricas');
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Nada publicado ainda');
  });

  it('renderiza métricas publicadas com destaque de alerta', () => {
    component.metricas.set([
      { id: 1, policy_id: 'linucb-v1', metric: 'psi_drift', value: 0.4, alert: true, created_at: '' },
    ]);
    component.trocarAba('metricas');
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('psi_drift');
    expect(texto).toContain('alerta');
  });

  it('renderiza a aba MLflow com o resumo do registry', () => {
    component.trocarAba('mlflow');
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Modelos registrados');
    expect(texto).toContain('linucb-v1');
    expect(texto).toContain('v2');
    expect(texto).toContain('Abrir em nova aba');
  });

  it('avisa quando não há política registrada', () => {
    component.politicas.set([]);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('seed_policies.py');
  });

  it('avisa quando não há ciclo aberto', () => {
    component.ciclos.set([]);
    component.trocarAba('ciclos');
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Nenhum ciclo aberto');
  });

  it('promover recarrega o estado', () => {
    component.promover('thompson-v1');
    expect(governanceMock.promote).toHaveBeenCalledWith('thompson-v1');
    // recarrega: policies é chamado no init e de novo após a ação
    expect(governanceMock.policies).toHaveBeenCalledTimes(2);
  });
});
