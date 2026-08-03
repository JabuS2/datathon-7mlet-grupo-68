import { Component } from '@angular/core';

interface PurchaseCategory {
  name: string;
  value: string;
  percentage: number;
}

@Component({
  selector: 'app-purchase-summary',
  standalone: true,
  templateUrl: './purchase-summary.html',
})
export class PurchaseSummary {
  readonly categories: PurchaseCategory[] = [
    {
      name: 'Alimentação',
      value: 'R$ 1.420,00',
      percentage: 45,
    },
    {
      name: 'Lazer & Viagens',
      value: 'R$ 2.100,00',
      percentage: 65,
    },
    {
      name: 'Serviços & Contas',
      value: 'R$ 890,00',
      percentage: 25,
    },
  ];
}
