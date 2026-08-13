import { Component } from '@angular/core';
import { ITransaction } from '../../../interfaces/itransaction';

const mockTransactions: ITransaction[] = [
  {
    date: '24 Out 2023',
    description: 'Transferência PIX Recebida',
    icon: 'payments',
    status: 'Concluído',
    value: 'R$ 15.000,00',
    positive: true,
  },
  {
    date: '23 Out 2023',
    description: 'Compra Cartão Black',
    icon: 'shopping_bag',
    status: 'Concluído',
    value: 'R$ 4.250,80',
  },
  {
    date: '22 Out 2023',
    description: 'Pagamento de Boleto',
    icon: 'receipt_long',
    status: 'Concluído',
    value: 'R$ 890,45',
  },
  {
    date: '21 Out 2023',
    description: 'Dividendos - PETR4',
    icon: 'trending_up',
    status: 'Concluído',
    value: 'R$ 1.120,50',
    positive: true,
  },
];

function randomValue(min: number, max: number): string {
  const value = Math.random() * (max - min) + min;

  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

@Component({
  selector: 'app-recent-transactions',
  imports: [],
  templateUrl: './recent-transactions.html',
  styleUrl: './recent-transactions.css',
})
export class RecentTransactions {
  transactions: ITransaction[] = Array.from({ length: 5 }, (_, index) => ({
    ...mockTransactions[index % mockTransactions.length],
    date: `${24 - (index % 24)} Ago 2026`,
    value: randomValue(50, 15000),
  }));

  viewAll(): void {
    console.log('Ver todas as transações');
  }
}
