import { ProductCategory } from './iinvestiment';

/** Item da carteira — `GET /api/v1/interests`. */
export interface IInterest {
  armId: string;
  productName: string;
  description: string;
  category: ProductCategory;
  /** Quantas vezes clicou. Repetir é mais interesse, não outro item. */
  cliques: number;
  ultimoClique: string;
}
