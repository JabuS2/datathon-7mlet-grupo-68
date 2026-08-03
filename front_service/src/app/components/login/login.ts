import { Component, inject, signal } from '@angular/core';
import { email, form, FormField, required } from '@angular/forms/signals';
import { ILoginRequest, ILoginResponse } from '../../interfaces/ilogin';
import { Login } from '../../services/login';
import { BaseTrack } from '../../services/base-track';
import { Auth } from '../../services/auth';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ErrorHandler } from '../../utils/error-handler';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormField],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent {
  private _snackBar = inject(MatSnackBar);
  private loginService = inject(Login);
  private baseTrack = inject(BaseTrack);
  private authService = inject(Auth);
  private router = inject(Router);

  private errorHandler = inject(ErrorHandler);

  showPassword = false;

  loginModel = signal<ILoginRequest>({
    email: '',
    password: '',
  });

  loginForm = form(this.loginModel, (schemaPath) => {
    required(schemaPath.email, { message: 'Email é requerido' });
    required(schemaPath.password, { message: 'Senha é requerida' });
    email(schemaPath.email, { message: 'Informe um email válido' });
  });

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(event: Event) {
    event.preventDefault();
    const credentials = this.loginModel();

    this.loginService
      .login(credentials)
      .pipe(this.baseTrack.track())
      .subscribe({
        next: (response: ILoginResponse) => {
          this.authService.setToken(response.accessToken, response.tokenType);
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          this._snackBar.open(this.errorHandler.getErrorMessage(error), 'Fechar', {
            duration: 3000,
            horizontalPosition: 'end',
            verticalPosition: 'top',
          });
        },
      });
  }
}
