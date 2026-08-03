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
  ],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css'],
})
export class DashboardComponent implements OnInit {
  private profileService = inject(Profile);

  profile = signal<IProfileResponse | null>(null);

  ngOnInit() {
    this.profileService.me().subscribe((profile) => {
      this.profile.set(profile);
    });
  }
}
