import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { IRegisterRequest, IRegisterResponse } from '../interfaces/iregister';
import { Observable } from 'rxjs';

@Service()
export class Register {
    private readonly _registerUrl = 'http://localhost:8008/api/v1/register';
    private http = inject(HttpClient);

    register(credentials: IRegisterRequest): Observable<IRegisterResponse> {
        return this.http.post<IRegisterResponse>(this._registerUrl, { email: credentials.email, password: credentials.password });
    }
}
