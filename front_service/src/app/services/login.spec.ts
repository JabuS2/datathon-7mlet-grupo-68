import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { Login } from './login';
import { ILoginRequest, ILoginResponse } from '../interfaces/ilogin';

describe('Login', () => {
  let service: Login;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Login, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(Login);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve fazer POST no endpoint de login com credenciais corretas', () => {
    const mockCredentials: ILoginRequest = {
      email: 'test@email.com',
      password: '123456',
    };

    const mockResponse: ILoginResponse = {
      accessToken: 'token123',
      tokenType: 'Bearer',
    };

    service.login(mockCredentials).subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne('http://localhost:8001/api/v1/login');

    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(mockCredentials);

    req.flush(mockResponse);
  });

  it('não deve chamar endpoint errado', () => {
    const mockCredentials: ILoginRequest = {
      email: 'test@email.com',
      password: '123456',
    };

    service.login(mockCredentials).subscribe();

    const req = httpMock.expectOne('http://localhost:8001/api/v1/login');

    expect(req.request.url).toContain('/login');
    req.flush({});
  });

  afterEach(() => {
    httpMock.verify();
    TestBed.resetTestingModule();
  });
});
