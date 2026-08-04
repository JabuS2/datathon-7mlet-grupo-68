import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { API_BASE_URL } from '../core/api';
import { SegmentoCliente } from '../interfaces/ionboarding';
import { Onboarding } from './onboarding';

describe('Onboarding', () => {
  let service: Onboarding;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Onboarding, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(Onboarding);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('completa o perfil da conta já autenticada, sem credenciais', () => {
    service
      .completeProfile({ idade: 26, segmento: SegmentoCliente.Varejo, possuiCartaoCredito: true })
      .subscribe();

    const req = httpMock.expectOne(API_BASE_URL + '/me/profile');
    expect(req.request.method).toBe('POST');
    // a tela é sobre perfil, não sobre criar conta
    expect(req.request.body).not.toHaveProperty('email');
    expect(req.request.body).not.toHaveProperty('password');
    expect(req.request.body.idade).toBe(26);
    req.flush({ codCliente: 9000001, idade: 26, segmentosSinteticos: [] });
  });
});
