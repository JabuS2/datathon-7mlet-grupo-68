import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { Auth } from './auth';

describe('Auth', () => {
  let service: Auth;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [Auth],
    });

    service = TestBed.inject(Auth);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve iniciar sem token quando o localStorage estiver vazio', () => {
    expect(service.token()).toBeNull();
    expect(service.hasValidToken()).toBe(false);
  });

  it('deve carregar o token do localStorage ao iniciar', () => {
    localStorage.setItem('accessToken', 'abc123');
    localStorage.setItem('tokenType', 'Bearer');

    const auth = TestBed.runInInjectionContext(() => new Auth());

    expect(auth.token()).toEqual({
      accessToken: 'abc123',
      tokenType: 'Bearer',
    });

    expect(auth.hasValidToken()).toBe(true);
  });

  it('deve salvar o token no localStorage e atualizar o signal', () => {
    service.setToken('abc123', 'Bearer');

    expect(localStorage.getItem('accessToken')).toBe('abc123');
    expect(localStorage.getItem('tokenType')).toBe('Bearer');

    expect(service.token()).toEqual({
      accessToken: 'abc123',
      tokenType: 'Bearer',
    });
  });

  it('deve remover o token do localStorage e limpar o signal', () => {
    service.setToken('abc123', 'Bearer');

    service.clearToken();

    expect(localStorage.getItem('accessToken')).toBeNull();
    expect(localStorage.getItem('tokenType')).toBeNull();
    expect(service.token()).toBeNull();
    expect(service.hasValidToken()).toBe(false);
  });

  it('deve retornar false quando não houver token', () => {
    expect(service.hasValidToken()).toBe(false);
  });

  it('deve retornar true quando houver token', () => {
    service.setToken('abc123', 'Bearer');

    expect(service.hasValidToken()).toBe(true);
  });

  it('deve iniciar sem token se accessToken existir mas tokenType não', () => {
    localStorage.setItem('accessToken', 'abc123');

    const auth = TestBed.runInInjectionContext(() => new Auth());

    expect(auth.token()).toBeNull();
  });

  it('deve iniciar sem token se tokenType existir mas accessToken não', () => {
    localStorage.setItem('tokenType', 'Bearer');

    const auth = TestBed.runInInjectionContext(() => new Auth());

    expect(auth.token()).toBeNull();
  });
});