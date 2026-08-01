import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { Register } from './register';
import { IRegisterRequest, IRegisterResponse } from '../interfaces/iregister';

describe('Register', () => {
  let service: Register;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Register, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(Register);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve fazer POST no endpoint de registro com payload correto', () => {
    const input: IRegisterRequest = {
      email: 'test@email.com',
      password: '123456',
      confirmPassword: '123456',
    };

    const mockResponse: IRegisterResponse = {
      email: input.email,
    };

    service.register(input).subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne('http://localhost:8001/api/v1/register');

    expect(req.request.method).toBe('POST');

    expect(req.request.body).toEqual({
      email: input.email,
      password: input.password,
    });

    req.flush(mockResponse);
  });

  afterEach(() => {
    httpMock.verify();
    TestBed.resetTestingModule();
  });
});
