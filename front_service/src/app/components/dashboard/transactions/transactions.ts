import { Component } from '@angular/core';

interface Transaction {
  date: string;
  description: string;
  icon: string;
  status: 'Concluído' | 'Processando';
  value: string;
  income: boolean;
}

@Component({
  selector: 'app-transactions',
  standalone: true,
  templateUrl: './transactions.html',
  styleUrls: ['./transactions.css'],
})
export class Transactions {
  readonly transactions: Transaction[] = this.generateTransactions();

  private generateTransactions(): Transaction[] {
    const descriptions = [
      { text: 'Transferência Recebida - PIX', icon: 'transfer_within_a_station', income: true },
      { text: 'Pagamento via PIX', icon: 'payments', income: false },
      { text: 'Supermercado Central', icon: 'shopping_cart', income: false },
      { text: 'Farmácia São João', icon: 'local_pharmacy', income: false },
      { text: 'Dividendos - PETR4', icon: 'trending_up', income: true },
      { text: 'Dividendos - ITUB4', icon: 'account_balance', income: true },
      { text: 'Restaurante', icon: 'restaurant', income: false },
      { text: 'Posto de Combustível', icon: 'local_gas_station', income: false },
      { text: 'Salário', icon: 'payments', income: true },
      { text: 'Compra Online', icon: 'shopping_bag', income: false },
    ];

    return Array.from({ length: 4 }, () => {
      const item = descriptions[Math.floor(Math.random() * descriptions.length)];
      const status: Transaction['status'] = Math.random() > 0.3 ? 'Concluído' : 'Processando';

      const amount = item.income ? this.random(80, 5000) : this.random(15, 1200);

      const date = new Date();
      date.setDate(date.getDate() - this.random(0, 10));

      return {
        date: date.toLocaleDateString('pt-BR', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
        }),
        description: item.text,
        icon: item.icon,
        status,
        value: `${item.income ? '' : '- '}R$ ${amount.toLocaleString('pt-BR', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`,
        income: item.income,
      };
    });
  }

  private random(min: number, max: number): number {
    return +(Math.random() * (max - min) + min).toFixed(2);
  }
}
