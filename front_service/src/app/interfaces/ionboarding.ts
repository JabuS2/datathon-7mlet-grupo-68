/**
 * Perguntas de perfil — corpo de `POST /me/profile`.
 *
 * **Sem credenciais**: a pessoa já se registrou e logou. Esta tela é sobre quem ela é, não
 * sobre criar conta; pedir email/senha de novo aqui misturaria as duas coisas.
 *
 * O backend sorteia um cliente real do golden set que case com as respostas e copia as 24
 * flags de posse de produto como template, preservando as correlações reais. As respostas
 * abaixo sobrescrevem o template — cada uma cobre um filtro que o catálogo lê na
 * elegibilidade, ou uma feature de contexto do LinUCB.
 *
 * Só `idade` e `segmento` são obrigatórios: o resto, omitido, vem do template. Quanto mais
 * a pessoa responde, menos o perfil depende do sorteio.
 */
export interface IOnboardingRequest {
  idade: number;
  /** Perfil declarado — usado para casar o template. */
  segmento: SegmentoCliente;

  rendaEstimadaAnualBrl?: number;
  tempoRelacionamentoMeses?: number;
  possuiCartaoCredito?: boolean;
  possuiFundoInvestimento?: boolean;
  possuiFinanciamentoImovel?: boolean;
}

export enum SegmentoCliente {
  AltaRenda = '01 - ALTA RENDA',
  Varejo = '02 - VAREJO',
  Universitario = '03 - UNIVERSITARIO',
}

/** `POST /me/profile` devolve o perfil criado — a conta já estava autenticada. */
export interface IOnboardingResponse {
  codCliente: number;
  idade: number;
  segmentosSinteticos: string[];
}
