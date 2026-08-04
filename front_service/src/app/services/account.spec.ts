import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { API_BASE_URL } from '../core/api';
import { Account, IAccount } from './account';

describe('Account', () => {
  let service: Account;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Account, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(Account);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lê a conta autenticada', () => {
    let recebido: IAccount | null = null;
    service.me().subscribe((me) => (recebido = me));

    const req = httpMock.expectOne(API_BASE_URL + '/me');
    expect(req.request.method).toBe('GET');
    req.flush({
      id: 7,
      email: 'op@x.com',
      tipo: 'operador',
      codCliente: null,
      saldoFicticio: null,
    });

    // `codCliente: null` é o sinal que o profileGuard usa para exigir onboarding
    expect(recebido).toMatchObject({ id: 7, tipo: 'operador', codCliente: null });
  });
});
