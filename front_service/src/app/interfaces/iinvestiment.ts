export interface RecommendationItem {
  armId: string;
  productName: string;
  description: string;
  category: ProductCategory;

  expectedRevenueBrl: number;

  contextFeatures: string[];

  eligibleSegment: EligibleSegment;

  ucbExplorationFactor: number;
}

export interface EligibleSegment {
  santander_filters: SantanderFilters;
}

export interface SantanderFilters {
  idade_min?: number;
  idade_max?: number;

  renda_percentil_min?: number;

  ind_ativo?: number;

  tempo_relacionamento_meses_min?: number;

  possui_conta_corrente?: number;
  possui_cartao_credito?: number;

  possui_emprestimo_pessoal_atual?: number;
  possui_cartao_credito_atual?: number;

  possui_conta_investimento?: number;
  possui_fundo_investimento?: number;

  possui_cdb_curto_prazo_atual?: number;
  possui_cdb_medio_prazo_atual?: number;

  possui_previdencia_privada_atual?: number;

  possui_financiamento_imovel_atual?: number;
}

export enum ProductCategory {
  Investimento = 'investimento',
  Seguro = 'seguro',
  Credito = 'credito',
}

export type RecommendationResponse = RecommendationItem[];
