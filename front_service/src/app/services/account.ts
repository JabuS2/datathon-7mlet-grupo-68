import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api';

/** `GET /api/v1/me` — a conta autenticada. */
export interface IAccount {
  /** Necessário para o approval gate, que registra quem aprovou. */
  id: number | null;
  email: string;
  tipo: string;
  /** `null` enquanto a pessoa não completou o perfil (é o sinal do profileGuard). */
  codCliente: number | null;
  saldoFicticio: number | null;
}

@Service()
export class Account {
  private readonly _meUrl = `${API_BASE_URL}/me`;
  private http = inject(HttpClient);

  me(): Observable<IAccount> {
    return this.http.get<IAccount>(this._meUrl);
  }
}
