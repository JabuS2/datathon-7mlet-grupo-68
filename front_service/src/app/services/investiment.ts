import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { RecommendationResponse } from '../interfaces/iinvestiment';
import { Observable } from 'rxjs';

@Service()
export class Investiment {
  private readonly _profileUrl = 'http://localhost:8008/api/v1/offers';
  private http = inject(HttpClient);

  recommendations(): Observable<RecommendationResponse> {
    return this.http.get<RecommendationResponse>(this._profileUrl);
  }
}
