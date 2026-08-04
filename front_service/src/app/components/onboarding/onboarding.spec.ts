import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SegmentoCliente } from '../../interfaces/ionboarding';
import { Onboarding } from '../../services/onboarding';
import { OnboardingComponent } from './onboarding';

describe('OnboardingComponent', () => {
  let component: OnboardingComponent;
  let fixture: ComponentFixture<OnboardingComponent>;

  const resposta = { codCliente: 9000001, idade: 24, segmentosSinteticos: ['SEG-JOVEM'] };

  const onboardingMock = { completeProfile: vi.fn().mockReturnValue(of(resposta)) };

  beforeEach(async () => {
    vi.clearAllMocks();
    localStorage.clear();

    await TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Onboarding, useValue: onboardingMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(OnboardingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('começa com respostas default para todas as perguntas opcionais', () => {
    const m = component.model();
    expect(m.rendaEstimadaAnualBrl).toBeGreaterThan(0);
    expect(m.tempoRelacionamentoMeses).toBeGreaterThan(0);
    expect(m.possuiCartaoCredito).toBe(false);
  });

  it('converte a string do select em número', () => {
    component.setRenda('90000');
    component.setTempo('42');
    expect(component.model().rendaEstimadaAnualBrl).toBe(90000);
    expect(component.model().tempoRelacionamentoMeses).toBe(42);
  });

  it('alterna as flags de posse', () => {
    component.toggle('possuiCartaoCredito');
    expect(component.model().possuiCartaoCredito).toBe(true);
    component.toggle('possuiCartaoCredito');
    expect(component.model().possuiCartaoCredito).toBe(false);
  });

  it('troca o segmento', () => {
    component.setSegmento(SegmentoCliente.AltaRenda);
    expect(component.model().segmento).toBe(SegmentoCliente.AltaRenda);
  });

  it('não pede credenciais: o modelo só tem perguntas de perfil', () => {
    // a conta já existe e está autenticada quando esta tela abre
    expect(component.model()).not.toHaveProperty('email');
    expect(component.model()).not.toHaveProperty('password');
  });

  it('envia as respostas e vai para a vitrine', () => {
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    component.onSubmit(new Event('submit'));

    expect(onboardingMock.completeProfile).toHaveBeenCalledOnce();
    expect(navigate).toHaveBeenCalledWith(['/dashboard']);
  });

  it('não navega quando o backend recusa', () => {
    onboardingMock.completeProfile.mockReturnValueOnce(
      throwError(() => ({ status: 409, error: { code: 'PROFILE_EXISTS' } })),
    );
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    component.onSubmit(new Event('submit'));

    expect(navigate).not.toHaveBeenCalled();
  });
});
