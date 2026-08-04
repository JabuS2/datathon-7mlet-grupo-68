import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api';
import { IFeedbackRequest, IFeedbackResponse } from '../interfaces/ifeedback';

@Service()
export class Feedback {
  private readonly _feedbackUrl = `${API_BASE_URL}/feedback`;
  private http = inject(HttpClient);

  /**
   * Registra o clique e realimenta o modelo.
   *
   * O api_service grava o evento e repassa ao model_service (`POST /update`), que atualiza
   * o estado do braço na política ativa. O próximo `GET /offers` já reflete o aprendizado —
   * é o loop compute-on-read do bandit.
   */
  click(armId: string): Observable<IFeedbackResponse> {
    const body: IFeedbackRequest = { armId, clicked: true };
    return this.http.post<IFeedbackResponse>(this._feedbackUrl, body);
  }
}
