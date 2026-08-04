/** Corpo de `POST /api/v1/feedback` — o clique que realimenta o bandit. */
export interface IFeedbackRequest {
  armId: string;
  clicked: boolean;
}

export interface IFeedbackResponse {
  armId: string;
  clicked: boolean;
  /** Binária: 1.0 com clique, 0.0 sem. */
  reward: number;
  algorithm: string;
  status: string;

  /** Quanto saiu do saldo (0 quando não há preço ou faltou saldo). */
  valorDebitado: number;
  /** Saldo já atualizado — a tela usa este valor em vez de recalcular. */
  saldoFicticio: number | null;
  /** Produto tem preço mas o saldo não cobria. O interesse é registrado mesmo assim. */
  saldoInsuficiente: boolean;
}
