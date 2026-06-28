import { Component, inject, signal } from '@angular/core';
import { email, form, FormField, minLength, required, validate } from '@angular/forms/signals';
import { IRegisterRequest } from '../../interfaces/iregister';
import { Register } from '../../services/register';
import { BaseTrack } from '../../services/base-track';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { ErrorHandler } from '../../utils/error-handler';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormField],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class RegisterComponent {
  private _snackBar = inject(MatSnackBar);
  private registerService = inject(Register);
  private baseTrack = inject(BaseTrack);
  private router = inject(Router);
  private errorHandler = inject(ErrorHandler);


  registerModel = signal<IRegisterRequest>({
    email: '',
    password: '',
    confirmPassword: '',
  });

  registerForm = form(this.registerModel, (schemaPath) => {
    required(schemaPath.email, { message: 'Email é requerido' });
    required(schemaPath.password, { message: 'Senha é requerida' });
    minLength(schemaPath.password, 8, { message: 'A senha deve ter no mínimo 8 caracteres' });
    required(schemaPath.confirmPassword, { message: 'Confirmação de senha é requerida' });
    email(schemaPath.email, { message: 'Informe um email válido' });
    validate(schemaPath.confirmPassword, ({ valueOf }) => {
      const password = valueOf(schemaPath.password);
      const confirm = valueOf(schemaPath.confirmPassword);

      if (password !== confirm) {
        return {
          kind: 'error',
          message: 'As senhas não conferem',
        };
      }

      return null;
    });
  });

  onSubmit(event: Event) {
    event.preventDefault();
    const credentials = this.registerModel();

    this.registerService.register(credentials).pipe(this.baseTrack.track()).subscribe({
      next: () => {
        this._snackBar.open('Registro realizado com sucesso!', 'Fechar', {
          duration: 3000,
          horizontalPosition: 'end',
          verticalPosition: 'top',
        });
        this.router.navigate(['/login']);
      },
      error: (error: HttpErrorResponse) => {
        this._snackBar.open(
          this.errorHandler.getErrorMessage(error),
          'Fechar',
          {
            duration: 3000,
            horizontalPosition: 'end',
            verticalPosition: 'top',
          }
        );
      }
    });
  }
}
