import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { Account } from '../services/account';

/**
 * Restringe o console de operação a contas `operador`.
 *
 * As rotas de monitoramento do api_service usam `require_operador`; sem este guard um
 * usuário `demo` abria a tela e recebia 403 em cada botão — parecia bug do console e era
 * papel errado. Melhor não deixar entrar.
 *
 * Isto é conveniência de navegação, não segurança: quem autoriza de verdade é o backend.
 */
export const operadorGuard: CanActivateFn = () => {
  const account = inject(Account);
  const router = inject(Router);

  return account.me().pipe(
    map((me) => (me.tipo === 'operador' ? true : router.createUrlTree(['/dashboard']))),
    catchError(() => of(router.createUrlTree(['/login']))),
  );
};
