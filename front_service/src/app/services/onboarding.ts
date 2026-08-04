import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api';
import { IOnboardingRequest, IOnboardingResponse } from '../interfaces/ionboarding';

@Service()
export class Onboarding {
  private readonly _profileUrl = `${API_BASE_URL}/me/profile`;
  private http = inject(HttpClient);

  /**
   * Anexa o perfil de cliente à conta já autenticada (segunda etapa do cadastro).
   *
   * Sem perfil o usuário é um operador sem `codCliente`, e a vitrine responde
   * `409 NO_CLIENT_PROFILE` — o bandit não tem contexto para ranquear.
   */
  completeProfile(answers: IOnboardingRequest): Observable<IOnboardingResponse> {
    return this.http.post<IOnboardingResponse>(this._profileUrl, answers);
  }
}
