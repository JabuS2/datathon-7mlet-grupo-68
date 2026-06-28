import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { beforeEach, describe, expect, it } from 'vitest';

import { ErrorHandler } from './error-handler';

describe('ErrorHandler', () => {
  let service: ErrorHandler;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ErrorHandler],
    });

    service = TestBed.inject(ErrorHandler);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve retornar mensagem de erro de conexão quando status for 0', () => {
    const error = new HttpErrorResponse({
      status: 0,
      statusText: 'Unknown Error',
    });

    expect(service.getErrorMessage(error)).toBe('Não foi possível conectar ao servidor.');
  });

  it('deve retornar error.error.error quando existir', () => {
    const error = new HttpErrorResponse({
      status: 400,
      error: { error: 'Erro de validação' },
    });

    expect(service.getErrorMessage(error)).toBe('Erro de validação');
  });

  it('deve retornar error.error.message quando error.error.error não existir', () => {
    const error = new HttpErrorResponse({
      status: 400,
      error: { message: 'Mensagem alternativa' },
    });

    expect(service.getErrorMessage(error)).toBe('Mensagem alternativa');
  });

  it('deve retornar error.message quando não houver error.error', () => {
    const error = new HttpErrorResponse({
      status: 500,
      error: { message: 'Erro do Http' },
    });

    expect(service.getErrorMessage(error)).toBe('Erro do Http');
  });

  it('deve retornar mensagem padrão quando não houver nada', () => {
    const error = new HttpErrorResponse({
      status: 500,
    });

    Object.defineProperty(error, 'message', {
      value: undefined,
    });

    expect(service.getErrorMessage(error)).toBe('Erro inesperado.');
  });
});
