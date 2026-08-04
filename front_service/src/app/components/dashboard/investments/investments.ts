import { DecimalPipe } from '@angular/common';
import { Component, computed, inject, OnInit, output, signal } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { delay, switchMap, tap } from 'rxjs';

import { RecommendationItem } from '../../../interfaces/iinvestiment';
import { Feedback } from '../../../services/feedback';
import { Investiment } from '../../../services/investiment';

/** Quantos cards aparecem antes de "Ver mais". */
export const TOP_VISIVEL = 4;

/**
 * Tempo que o card fica marcado como escolhido antes da lista se reordenar.
 *
 * Sem essa pausa o clique parece não ter efeito: o reload chega tão rápido que a pessoa vê
 * a lista pular sem entender o que aconteceu. A confirmação visual vem primeiro, o
 * reordenamento depois.
 */
export const CONFIRMACAO_MS = 900;

@Component({
  selector: 'app-investments',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './investments.html',
})
export class InvestmentOpportunitiesComponent implements OnInit {
  private investimentService = inject(Investiment);
  private feedbackService = inject(Feedback);
  private _snackBar = inject(MatSnackBar);

  /** Avisa o dashboard: carteira mudou e o saldo foi debitado. */
  interesseRegistrado = output<{ armId: string; saldo: number | null }>();

  opportunities = signal<RecommendationItem[]>([]);
  expandido = signal(false);
  /** Trava enquanto o clique é processado — evita reward duplicado no mesmo braço. */
  enviando = signal<string | null>(null);
  /** Card marcado como escolhido, exibindo a confirmação antes do reload. */
  escolhido = signal<string | null>(null);

  /**
   * Ranking do modelo com os já adquiridos empurrados para o fim.
   *
   * O backend devolve o ranking completo: a ordem é do bandit. Aqui só garantimos que o
   * que a pessoa pode contratar apareça primeiro — sem remover nada, senão a vitrine
   * esvazia quando o catálogo se esgota e parece que o modelo parou de recomendar.
   */
  ordenadas = computed(() => [
    ...this.opportunities().filter((o) => !o.jaAdquirida),
    ...this.opportunities().filter((o) => o.jaAdquirida),
  ]);

  /** O que a vitrine mostra: top 4, ou tudo quando expandida. */
  visiveis = computed(() =>
    this.expandido() ? this.ordenadas() : this.ordenadas().slice(0, TOP_VISIVEL),
  );

  /**
   * Quantas ofertas **contratáveis** ficaram fora do top 4.
   *
   * Conta só as não adquiridas: "Ver mais 3 ofertas" quando as três são produtos que a
   * pessoa já tem é uma promessa que a expansão não cumpre. Como as adquiridas ficam no
   * fim de `ordenadas`, as escondidas são justamente as que sobram depois do corte.
   */
  ocultas = computed(() =>
    this.ordenadas()
      .slice(TOP_VISIVEL)
      .filter((o) => !o.jaAdquirida).length,
  );

  ngOnInit(): void {
    this.investimentService.recommendations().subscribe((response) => {
      this.opportunities.set(response);
    });
  }

  toggleExpandir(): void {
    this.expandido.update((v) => !v);
  }

  /**
   * Clique no card: registra o feedback e **recarrega a vitrine**.
   *
   * É o loop do bandit fechando na tela. O reward vai para o model_service, que atualiza o
   * estado do braço; o `GET /offers` seguinte já vem reordenado. Sem recarregar, o clique
   * não teria efeito visível — era o que acontecia antes, quando isto só dava `console.log`.
   */
  knowMore(opportunity: RecommendationItem): void {
    if (this.enviando() || opportunity.jaAdquirida) return;
    this.enviando.set(opportunity.armId);

    this.feedbackService
      .click(opportunity.armId)
      .pipe(
        // marca o card ANTES de recarregar: a pessoa vê o que escolheu
        tap((resp) => {
          this.escolhido.set(opportunity.armId);
          this.interesseRegistrado.emit({
            armId: opportunity.armId,
            saldo: resp.saldoFicticio,
          });
          if (resp.saldoInsuficiente) {
            this._snackBar.open(
              'Saldo insuficiente — registramos seu interesse mesmo assim.',
              'Fechar',
              { duration: 4000, horizontalPosition: 'end', verticalPosition: 'top' },
            );
          }
        }),
        delay(CONFIRMACAO_MS),
        switchMap(() => this.investimentService.recommendations()),
      )
      .subscribe({
        next: (response) => {
          this.opportunities.set(response);
          this.escolhido.set(null);
          this.enviando.set(null);
          this._snackBar.open(
            `"${opportunity.productName}" foi para a sua carteira.`,
            'Fechar',
            { duration: 3000, horizontalPosition: 'end', verticalPosition: 'top' },
          );
        },
        error: () => {
          this.escolhido.set(null);
          this.enviando.set(null);
          this._snackBar.open('Não foi possível registrar seu interesse.', 'Fechar', {
            duration: 3000,
            horizontalPosition: 'end',
            verticalPosition: 'top',
          });
        },
      });
  }
}
