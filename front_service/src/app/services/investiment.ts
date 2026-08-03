import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { RecommendationResponse } from '../interfaces/iinvestiment';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api';

@Service()
export class Investiment {
  private readonly _offersUrl = `${API_BASE_URL}/offers`;
  private http = inject(HttpClient);

  recommendations(): Observable<RecommendationResponse> {
    return this.http.get<RecommendationResponse>(this._offersUrl);
  }
}
