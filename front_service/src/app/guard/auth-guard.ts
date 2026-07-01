import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth } from '../services/auth';

export const authGuard: CanActivateFn = (_route, _state) => {
  const auth = inject(Auth)
  const router = inject(Router)

  if (!auth.hasValidToken()) {
    return router.createUrlTree(['/login']);
  }

  return true;
};
