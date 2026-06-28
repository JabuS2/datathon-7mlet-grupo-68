import { Service, signal } from '@angular/core';
import { ILoginResponse } from '../interfaces/ilogin';

@Service()
export class Auth {
    private tokenSignal = signal<ILoginResponse | null>(this.getInitialToken());

    private getInitialToken(): ILoginResponse | null {
        const token = localStorage.getItem('accessToken');
        const type = localStorage.getItem('tokenType');

        if (!token || !type) return null;

        return { accessToken: token, tokenType: type };
    }

    readonly token = this.tokenSignal.asReadonly();

    setToken(token: string, type: string): void {
        localStorage.setItem('accessToken', token);
        localStorage.setItem('tokenType', type);
        this.tokenSignal.set({ accessToken: token, tokenType: type });
    }

    clearToken(): void {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('tokenType');
        this.tokenSignal.set(null);
    }

    hasValidToken(): boolean {
        const token = this.token();
        if (!token) return false;

        return true;
    }
}
