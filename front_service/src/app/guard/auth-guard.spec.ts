import { TestBed } from '@angular/core/testing';
import {
  CanActivateFn,
  Router,
  UrlTree,
} from '@angular/router';
import { describe, beforeEach, expect, it, vi } from 'vitest';

import { authGuard } from './auth-guard';
import { Auth } from '../services/auth';

describe('authGuard', () => {
  const authMock = {
    hasValidToken: vi.fn(),
  };

  const urlTreeMock = {} as UrlTree;

  const routerMock = {
    createUrlTree: vi.fn(),
  };

  const executeGuard: CanActivateFn = (...guardParameters) =>
    TestBed.runInInjectionContext(() => authGuard(...guardParameters));

  beforeEach(() => {
    vi.clearAllMocks();

    routerMock.createUrlTree.mockReturnValue(urlTreeMock);

    TestBed.configureTestingModule({
      providers: [
        {
          provide: Auth,
          useValue: authMock,
        },
        {
          provide: Router,
          useValue: routerMock,
        },
      ],
    });
  });

  it('deve permitir acesso quando o token for válido', () => {
    authMock.hasValidToken.mockReturnValue(true);

    const result = executeGuard({} as any, {} as any);

    expect(result).toBe(true);
    expect(authMock.hasValidToken).toHaveBeenCalledOnce();
    expect(routerMock.createUrlTree).not.toHaveBeenCalled();
  });

  it('deve redirecionar para login quando o token for inválido', () => {
    authMock.hasValidToken.mockReturnValue(false);

    const result = executeGuard({} as any, {} as any);

    expect(authMock.hasValidToken).toHaveBeenCalledOnce();
    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/login']);
    expect(result).toBe(urlTreeMock);
  });
});