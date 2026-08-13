import { Component, inject, OnInit, signal } from '@angular/core';
import { TopbarComponent } from '../../shared/topbar/topbar';
import { Profile } from '../../../services/profile';
import { IProfileResponse } from '../../../interfaces/iprofile';
import { SidebarComponent } from '../../shared/sidebar/sidebar';
import { RecentTransactions } from '../recent-transactions/recent-transactions';
import { FutureTransactionsComponent } from '../future-transactions/future-transactions';
import { WalletComponent } from '../../dashboard/wallet/wallet';

@Component({
  selector: 'app-investiments-component',
  imports: [
    TopbarComponent,
    SidebarComponent,
    RecentTransactions,
    FutureTransactionsComponent,
    WalletComponent,
  ],
  templateUrl: './investiments-component.html',
  styleUrl: './investiments-component.css',
})
export class InvestimentsComponent implements OnInit {
  private profileService = inject(Profile);

  profile = signal<IProfileResponse | null>(null);

  ngOnInit() {
    this.profileService.me().subscribe((profile) => {
      this.profile.set(profile);
    });
  }
}
