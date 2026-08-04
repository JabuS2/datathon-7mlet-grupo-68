import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Account } from '../services/account';
import { operadorGuard } from './operador-guard';

function rodar(): unknown {
  return TestBed.runInInjectionContext(() => operadorGuard({} as never, {} as never));
}

function resolver(): Promise<unknown> {
  return new Promise((resolve) =>
    (rodar() as never as { subscribe: (f: unknown) => void }).subscribe(resolve),
  );
}

describe('operadorGuard', () => {
  const accountMock = { me: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: Account, useValue: accountMock }],
    });
  });

  it('deixa o operador entrar no console', async () => {
    accountMock.me.mockReturnValue(
      of({ id: 1, email: 'op@x.com', tipo: 'operador', codCliente: null, saldoFicticio: null }),
    );

    expect(await resolver()).toBe(true);
  });

  it('manda o demo de volta — o backend também recusaria com 403', async () => {
    accountMock.me.mockReturnValue(
      of({ id: 2, email: 'd@x.com', tipo: 'demo', codCliente: 900, saldoFicticio: 100 }),
    );

    const resultado = await resolver();

    expect(resultado).toBeInstanceOf(UrlTree);
    expect(TestBed.inject(Router).serializeUrl(resultado as UrlTree)).toBe('/dashboard');
  });

  it('sem sessão válida, volta para o login', async () => {
    accountMock.me.mockReturnValue(throwError(() => new Error('401')));

    const resultado = await resolver();

    expect(TestBed.inject(Router).serializeUrl(resultado as UrlTree)).toBe('/login');
  });
});
