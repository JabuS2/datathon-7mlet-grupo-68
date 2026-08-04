/**
 * Contrato de `GET /api/v1/offers` — a vitrine ranqueada pelo model_service.
 *
 * Espelha o `OfferResponse` do api_service. Receita esperada, features de contexto e regras de
 * elegibilidade NÃO vêm mais aqui: são parâmetros internos do bandit, restritos a operador em
 * `/offers/catalog`.
 */
export interface RecommendationItem {
  armId: string;
  /** Posição no ranking do bandit (1 = melhor oferta para este cliente). */
  rank: number;
  /** Score da política — quanto maior, mais o modelo aposta nesta oferta. */
  score: number;
  productName: string;
  description: string;
  category: ProductCategory;

  /**
   * Valores comerciais da oferta. Opcionais: a API serializa com
   * `response_model_exclude_none`, então campos sem valor vêm ausentes, não nulos.
   */
  valorTotal?: number;
  descontoPct?: number;
  valorFinal?: number;

  /** Já está na carteira — o card aparece, mas não convida a clicar de novo. */
  jaAdquirida: boolean;
}

export enum ProductCategory {
  Investimento = 'investimento',
  Seguro = 'seguro',
  Credito = 'credito',
}

export type RecommendationResponse = RecommendationItem[];
