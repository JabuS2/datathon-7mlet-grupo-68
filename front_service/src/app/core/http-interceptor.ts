import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Auth } from '../services/auth';

export const httpInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(Auth);
  const token = auth.token();

  if (!token?.accessToken) {
    return next(req);
  }

  const authReq = req.clone({
    setHeaders: {
      Authorization: `${token.tokenType} ${token.accessToken}`,
    },
  });

  return next(authReq);
};