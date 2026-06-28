import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { Admin } from './components/admin/admin';
import { authGuard } from './guard/auth-guard';
import { RegisterComponent } from './components/register/register';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'register',
    component: RegisterComponent,
  },
  {
    path: 'admin',
    component: Admin,
    canActivate: [authGuard],
  },
];
