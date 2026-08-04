import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Account } from '../services/account';
import { profileGuard } from './profile-guard';

/** Executa o guard dentro do contexto de injeção, como o router faria. */
function rodar(): unknown {
  return TestBed.runInInjectionContext(() =>
    profileGuard({} as never, {} as never),
  );
}

describe('profileGuard', () => {
  const accountMock = { me: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: Account, useValue: accountMock }],
    });
  });

  it('deixa passar quem tem perfil de cliente', async () => {
    accountMock.me.mockReturnValue(of({ id: 1, email: 'a@b.c', tipo: 'demo', codCliente: 900, saldoFicticio: 10 }));

    const resultado = await new Promise((resolve) => (rodar() as never as { subscribe: (f: unknown) => void }).subscribe(resolve));

    expect(resultado).toBe(true);
  });

  it('manda para o onboarding quem não tem `codCliente`', async () => {
    accountMock.me.mockReturnValue(of({ id: 1, email: 'a@b.c', tipo: 'operador', codCliente: null, saldoFicticio: null }));

    const resultado = await new Promise((resolve) => (rodar() as never as { subscribe: (f: unknown) => void }).subscribe(resolve));

    expect(resultado).toBeInstanceOf(UrlTree);
    expect(TestBed.inject(Router).serializeUrl(resultado as UrlTree)).toBe('/onboarding');
  });

  it('falha na checagem não tranca a navegação', async () => {
    // deixa passar e a própria tela mostra o erro — melhor que um loop de redirecionamento
    accountMock.me.mockReturnValue(throwError(() => new Error('offline')));

    const resultado = await new Promise((resolve) => (rodar() as never as { subscribe: (f: unknown) => void }).subscribe(resolve));

    expect(resultado).toBe(true);
  });
});
