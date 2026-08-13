import { Component } from '@angular/core';
import { IFutureTransaction } from '../../../interfaces/ifuturetransaction';

const mockTransactions: IFutureTransaction[] = [
  {
    date: '05 Out 2023',
    description: 'Fatura Cartão de Crédito',
    icon: 'event',
    status: 'Agendado',
    value: 'R$ 12.400,00',
  },
  {
    date: '10 Out 2023',
    description: 'Transferência Programada TED',
    icon: 'account_balance',
    status: 'Agendado',
    value: 'R$ 5.000,00',
  },
  {
    date: '15 Out 2023',
    description: 'Pagamento de Boleto',
    icon: 'receipt_long',
    status: 'Agendado',
    value: 'R$ 850,00',
  },
  {
    date: '20 Out 2023',
    description: 'Pagamento de Aluguel',
    icon: 'home',
    status: 'Agendado',
    value: 'R$ 2.800,00',
  },
  {
    date: '25 Out 2023',
    description: 'Transferência PIX Programada',
    icon: 'send',
    status: 'Agendado',
    value: 'R$ 1.500,00',
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
  selector: 'app-future-transactions',
  standalone: true,
  templateUrl: './future-transactions.html',
  styleUrls: ['./future-transactions.css'],
})
export class FutureTransactionsComponent {
  transactions: IFutureTransaction[] = Array.from({ length: 5 }, (_, index) => ({
    ...mockTransactions[index % mockTransactions.length],
    value: randomValue(100, 15000),
  }));
}
