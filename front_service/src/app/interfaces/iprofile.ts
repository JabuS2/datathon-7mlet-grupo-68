import { IBase } from './ibase';

export interface IProfileResponse extends IBase {
  codCliente: number;
  idade: number;
  tempoRelacionamentoMeses: number;
  indAtivo: boolean;
  segmento: string;
  estado: string;
  segmentosSinteticos: string[];
  origem: string;
  rendaEstimadaAnualBrl: number;
  /** `null` em perfis criados antes de o saldo passar a ser preenchido. */
  saldoFicticio: number | null;

  produtos: IProdutosCliente;
}

export interface IProdutosCliente {
  possuiPoupanca: boolean;
  possuiContaCorrente: boolean;
  possuiContaCorrentePlus: boolean;
  possuiContaPremium: boolean;
  possuiContaSalario: boolean;
  possuiContaJunior: boolean;
  possuiContaUniversitaria: boolean;
  possuiContaDigital: boolean;
  possuiContaInvestimento: boolean;

  possuiCdbCurtoPrazo: boolean;
  possuiCdbMedioPrazo: boolean;
  possuiCdbLongoPrazo: boolean;
  possuiFundoInvestimento: boolean;
  possuiTitulosInvestimento: boolean;
  possuiPrevidenciaPrivada: boolean;

  possuiFinanciamentoImovel: boolean;
  possuiFinanciamentoVeiculo: boolean;
  possuiEmprestimoPessoal: boolean;
  possuiCartaoCredito: boolean;
  possuiAvalGarantia: boolean;

  possuiPagamentoTributos: boolean;
  possuiFolhaPagamento: boolean;
  possuiBeneficioPrevidencia: boolean;
  possuiDebitoAutomatico: boolean;
}
