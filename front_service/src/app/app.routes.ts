import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { Admin } from './components/admin/admin';
import { authGuard } from './guard/auth-guard';
import { profileGuard } from './guard/profile-guard';
import { RegisterComponent } from './components/register/register';
import { OnboardingComponent } from './components/onboarding/onboarding';
import { DashboardComponent } from './components/dashboard/dashboard';
import { ProfileComponent } from './components/profile/profile';

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
    // Segunda etapa do cadastro: a conta já existe e está autenticada; aqui só as
    // perguntas de perfil. Sem perfil, a vitrine devolve 409 NO_CLIENT_PROFILE.
    path: 'onboarding',
    component: OnboardingComponent,
    canActivate: [authGuard],
  },
  {
    path: 'admin',
    component: Admin,
    canActivate: [authGuard],
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard, profileGuard],
  },
  {
    path: 'profile',
    component: ProfileComponent,
    canActivate: [authGuard, profileGuard],
  },
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: 'login',
  },
];
