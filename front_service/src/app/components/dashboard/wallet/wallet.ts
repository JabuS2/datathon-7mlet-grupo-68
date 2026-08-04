import { Component, inject, input, OnChanges, signal } from '@angular/core';

import { IInterest } from '../../../interfaces/iinterest';
import { Investiment } from '../../../services/investiment';

@Component({
  selector: 'app-wallet',
  standalone: true,
  imports: [],
  templateUrl: './wallet.html',
})
export class WalletComponent implements OnChanges {
  private investimentService = inject(Investiment);

  /**
   * Muda sempre que a vitrine registra um clique. Serve só como gatilho de recarga: a
   * carteira é derivada de `feedback_events` no backend, então quem manda é a API, não um
   * estado local que poderia divergir do que o modelo enxerga.
   */
  refreshKey = input<number>(0);

  itens = signal<IInterest[]>([]);

  ngOnChanges(): void {
    this.carregar();
  }

  private carregar(): void {
    this.investimentService.interests().subscribe((itens) => this.itens.set(itens));
  }
}
