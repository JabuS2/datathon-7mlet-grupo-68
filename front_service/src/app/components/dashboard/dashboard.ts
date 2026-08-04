import { Component, inject, OnInit, signal } from '@angular/core';
import { SidebarComponent } from '../shared/sidebar/sidebar';
import { TopbarComponent } from '../shared/topbar/topbar';
import { HeroMetricsComponent } from './hero-metrics/hero-metrics';
import { ProductsCardComponent } from './products-card/products-card';
import { SegmentsCardComponent } from './segments-card/segments-card';
import { IProfileResponse } from '../../interfaces/iprofile';
import { Profile } from '../../services/profile';
import { InvestmentOpportunitiesComponent } from './investments/investments';
import { Transactions } from './transactions/transactions';
import { WalletComponent } from './wallet/wallet';

@Component({
  selector: 'app-dashboard',
  imports: [
    SidebarComponent,
    TopbarComponent,
    HeroMetricsComponent,
    ProductsCardComponent,
    SegmentsCardComponent,
    InvestmentOpportunitiesComponent,
    Transactions,
    WalletComponent,
  ],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css'],
})
export class DashboardComponent implements OnInit {
  private profileService = inject(Profile);

  profile = signal<IProfileResponse | null>(null);
  /** Incrementa a cada interesse registrado — faz a carteira reler da API. */
  carteiraVersao = signal(0);

  /**
   * Atualiza carteira e saldo depois de uma compra.
   *
   * O saldo vem da resposta do feedback — quem debita é o servidor, com o preço do
   * catálogo. Recalcular aqui abriria espaço para a tela divergir do banco.
   */
  aoRegistrarInteresse(evento: { armId: string; saldo: number | null }): void {
    this.carteiraVersao.update((v) => v + 1);
    if (evento.saldo === null) return;
    this.profile.update((p) => (p ? { ...p, saldoFicticio: evento.saldo } : p));
  }

  ngOnInit() {
    this.profileService.me().subscribe((profile) => {
      this.profile.set(profile);
    });
  }
}
