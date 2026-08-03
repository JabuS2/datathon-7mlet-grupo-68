import { Component, inject, OnInit, signal } from '@angular/core';
import { SidebarComponent } from '../shared/sidebar/sidebar';
import { TopbarComponent } from '../shared/topbar/topbar';
import { IProfileResponse } from '../../interfaces/iprofile';
import { Profile } from '../../services/profile';
import { ProfileHeaderComponent } from './profile-header/profile-header';
import { ProfileCardComponent } from './profile-card/profile-card';
import { IncomeCardComponent } from '../dashboard/income-card/income-card';
import { ProductsCardComponent } from '../dashboard/products-card/products-card';
import { HeroMetricsComponent } from '../dashboard/hero-metrics/hero-metrics';
import { PurchaseSummary } from '../dashboard/purchase-summary/purchase-summary';
import { Transactions } from '../dashboard/transactions/transactions';

@Component({
  selector: 'app-profile',
  imports: [
    SidebarComponent,
    TopbarComponent,
    ProfileHeaderComponent,
    ProfileCardComponent,
    IncomeCardComponent,
    ProductsCardComponent,
    HeroMetricsComponent,
    PurchaseSummary,
    Transactions,
  ],
  standalone: true,
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class ProfileComponent implements OnInit {
  private profileService = inject(Profile);

  profile = signal<IProfileResponse | null>(null);

  ngOnInit() {
    this.profileService.me().subscribe((profile) => {
      this.profile.set(profile);
    });
  }
}
