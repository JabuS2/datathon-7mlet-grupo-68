import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { Admin } from './components/admin/admin';
import { authGuard } from './guard/auth-guard';
import { operadorGuard } from './guard/operador-guard';
import { profileGuard } from './guard/profile-guard';
import { RegisterComponent } from './components/register/register';
import { OnboardingComponent } from './components/onboarding/onboarding';
import { DashboardComponent } from './components/dashboard/dashboard';
import { ProfileComponent } from './components/profile/profile';
import { InvestimentsComponent } from './components/investiments/investiments-component/investiments-component';

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
    // Console de operação do modelo — só operador (o backend também recusa `demo`).
    path: 'admin',
    component: Admin,
    canActivate: [authGuard, operadorGuard],
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
    path: 'investments',
    component: InvestimentsComponent,
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
