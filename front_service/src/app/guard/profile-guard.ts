import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { Account } from '../services/account';

/**
 * Exige perfil de cliente antes das telas que dependem do bandit.
 *
 * Sem `codCliente` a conta é um operador: a vitrine responde `409 NO_CLIENT_PROFILE`,
 * porque o modelo não tem contexto para ranquear. Em vez de mostrar uma tela vazia ou um
 * erro, mandamos completar o perfil.
 *
 * Guard e não redirect no login: cobre também quem entra direto pela URL ou volta com a
 * sessão já aberta.
 */
export const profileGuard: CanActivateFn = () => {
  const account = inject(Account);
  const router = inject(Router);

  return account.me().pipe(
    map((me) => (me.codCliente ? true : router.createUrlTree(['/onboarding']))),
    // falha na checagem não pode trancar a navegação: deixa passar e a própria tela
    // mostra o erro da API, em vez de um loop de redirecionamento
    catchError(() => of(true)),
  );
};
