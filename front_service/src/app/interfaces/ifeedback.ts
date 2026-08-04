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
}
