import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { API_BASE_URL } from '../core/api';
import { IFeedbackResponse } from '../interfaces/ifeedback';
import { Feedback } from './feedback';

describe('Feedback', () => {
  let service: Feedback;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Feedback, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(Feedback);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('envia o clique que realimenta o bandit', () => {
    let resposta: IFeedbackResponse | null = null;
    service.click('OFF-CR-001').subscribe((r) => (resposta = r));

    const req = httpMock.expectOne(API_BASE_URL + '/feedback');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ armId: 'OFF-CR-001', clicked: true });

    req.flush({
      armId: 'OFF-CR-001',
      clicked: true,
      reward: 1,
      algorithm: 'linucb',
      status: 'applied',
      valorDebitado: 175,
      saldoFicticio: 8000,
      saldoInsuficiente: false,
    });

    // o saldo vem do servidor: quem debita é ele, com o preço do catálogo
    expect(resposta).toMatchObject({ valorDebitado: 175, saldoFicticio: 8000 });
  });

  it('propaga saldo insuficiente sem falhar', () => {
    let resposta: IFeedbackResponse | null = null;
    service.click('OFF-INV-004').subscribe((r) => (resposta = r));

    httpMock.expectOne(API_BASE_URL + '/feedback').flush({
      armId: 'OFF-INV-004',
      clicked: true,
      reward: 1,
      algorithm: 'linucb',
      status: 'applied',
      valorDebitado: 0,
      saldoFicticio: 10,
      saldoInsuficiente: true,
    });

    // o interesse é registrado mesmo sem saldo — o bandit precisa aprender com o clique
    expect(resposta).toMatchObject({ saldoInsuficiente: true, reward: 1 });
  });
});
