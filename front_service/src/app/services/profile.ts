import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { IProfileResponse } from '../interfaces/iprofile';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api';

@Service()
export class Profile {
  private readonly _profileUrl = `${API_BASE_URL}/me/profile`;
  private http = inject(HttpClient);

  me(): Observable<IProfileResponse> {
    return this.http.get<IProfileResponse>(this._profileUrl);
  }
}
