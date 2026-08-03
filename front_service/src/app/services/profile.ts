import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { IProfileResponse } from '../interfaces/iprofile';
import { Observable } from 'rxjs';

@Service()
export class Profile {
  private readonly _profileUrl = 'http://localhost:8008/api/v1/me/profile';
  private http = inject(HttpClient);

  me(): Observable<IProfileResponse> {
    return this.http.get<IProfileResponse>(this._profileUrl);
  }
}
