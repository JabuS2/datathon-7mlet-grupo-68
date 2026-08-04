import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { ILoginRequest, ILoginResponse } from '../interfaces/ilogin';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api';

@Service()
export class Login {
    private readonly _loginUrl = `${API_BASE_URL}/login`;
    private http = inject(HttpClient);

    login(credentials: ILoginRequest): Observable<ILoginResponse> {
        return this.http.post<ILoginResponse>(this._loginUrl, credentials);
    }
}