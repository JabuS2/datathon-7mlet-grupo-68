import { HttpErrorResponse } from '@angular/common/http';
import { Service } from '@angular/core';

@Service()
export class ErrorHandler {
  getErrorMessage(error: HttpErrorResponse): string {
    if (error.status === 0) {
      return 'Não foi possível conectar ao servidor.';
    }

    return error.error?.error ?? error.error?.message ?? error.message ?? 'Erro inesperado.';
  }
}
