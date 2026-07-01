import {
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest,
  HttpResponse,
} from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { describe, beforeEach, expect, it, vi } from 'vitest';

import { httpInterceptor } from './http-interceptor';
import { Auth } from '../services/auth';

describe('httpInterceptor', () => {
  const authMock = {
    token: vi.fn(),
  };

  const interceptor: HttpInterceptorFn = (req, next) =>
    TestBed.runInInjectionContext(() => httpInterceptor(req, next));

  beforeEach(() => {
    vi.clearAllMocks();

    TestBed.configureTestingModule({
      providers: [
        {
          provide: Auth,
          useValue: authMock,
        },
      ],
    });
  });

  it('deve seguir a requisição sem Authorization quando não houver token', () => {
    authMock.token.mockReturnValue(undefined);

    const request = new HttpRequest('GET', '/api/test');

    const next: HttpHandlerFn = (req) => {
      expect(req.headers.has('Authorization')).toBe(false);
      return of(new HttpResponse({ status: 200 }));
    };

    interceptor(request, next).subscribe();
  });

  it('deve adicionar o header Authorization quando houver token', () => {
    authMock.token.mockReturnValue({
      accessToken: 'abc123',
      tokenType: 'Bearer',
    });

    const request = new HttpRequest('GET', '/api/test');

    const next: HttpHandlerFn = (req) => {
      expect(req.headers.get('Authorization')).toBe('Bearer abc123');
      return of(new HttpResponse({ status: 200 }));
    };

    interceptor(request, next).subscribe();
  });

  it('não deve adicionar Authorization quando accessToken estiver vazio', () => {
    authMock.token.mockReturnValue({
      accessToken: '',
      tokenType: 'Bearer',
    });

    const request = new HttpRequest('GET', '/api/test');

    const next: HttpHandlerFn = (req) => {
      expect(req.headers.has('Authorization')).toBe(false);
      return of(new HttpResponse({ status: 200 }));
    };

    interceptor(request, next).subscribe();
  });
});