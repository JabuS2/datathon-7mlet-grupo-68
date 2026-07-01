import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { ILoginRequest, ILoginResponse } from '../interfaces/ilogin';
import { Observable } from 'rxjs';

@Service()
export class Login {
    private readonly _loginUrl = 'http://localhost:8008/api/v1/login';
    private http = inject(HttpClient);

    login(credentials: ILoginRequest): Observable<ILoginResponse> {
        return this.http.post<ILoginResponse>(this._loginUrl, credentials);
    }
}