import { Component, computed, input } from '@angular/core';
import { IProdutosCliente, IProfileResponse } from '../../../interfaces/iprofile';

type ProductKey = keyof IProdutosCliente;

@Component({
  selector: 'app-products-card',
  standalone: true,
  templateUrl: './products-card.html',
})
export class ProductsCardComponent {
  profile = input.required<IProfileResponse>();

  private readonly productConfig: {
    key: ProductKey;
    name: string;
    icon: string;
  }[] = [
    { key: 'possuiPoupanca', name: 'Poupança', icon: 'savings' },
    { key: 'possuiContaCorrente', name: 'Conta Corrente', icon: 'account_balance' },
    { key: 'possuiContaCorrentePlus', name: 'Conta Corrente Plus', icon: 'account_balance_wallet' },
    { key: 'possuiContaPremium', name: 'Conta Premium', icon: 'workspace_premium' },
    { key: 'possuiContaSalario', name: 'Conta Salário', icon: 'payments' },
    { key: 'possuiContaJunior', name: 'Conta Júnior', icon: 'child_care' },
    { key: 'possuiContaUniversitaria', name: 'Conta Universitária', icon: 'school' },
    { key: 'possuiContaDigital', name: 'Conta Digital', icon: 'smartphone' },
    { key: 'possuiContaInvestimento', name: 'Conta Investimento', icon: 'monitoring' },
    { key: 'possuiCdbCurtoPrazo', name: 'CDB Curto Prazo', icon: 'schedule' },
    { key: 'possuiCdbMedioPrazo', name: 'CDB Médio Prazo', icon: 'event' },
    { key: 'possuiCdbLongoPrazo', name: 'CDB Longo Prazo', icon: 'calendar_month' },
    { key: 'possuiFundoInvestimento', name: 'Fundo de Investimento', icon: 'candlestick_chart' },
    { key: 'possuiTitulosInvestimento', name: 'Títulos de Investimento', icon: 'query_stats' },
    { key: 'possuiPrevidenciaPrivada', name: 'Previdência Privada', icon: 'security' },
    { key: 'possuiFinanciamentoImovel', name: 'Financiamento de Imóvel', icon: 'home' },
    { key: 'possuiFinanciamentoVeiculo', name: 'Financiamento de Veículo', icon: 'directions_car' },
    { key: 'possuiEmprestimoPessoal', name: 'Empréstimo Pessoal', icon: 'payments' },
    { key: 'possuiCartaoCredito', name: 'Cartão de Crédito', icon: 'credit_card' },
    { key: 'possuiAvalGarantia', name: 'Aval / Garantia', icon: 'verified_user' },
    { key: 'possuiPagamentoTributos', name: 'Pagamento de Tributos', icon: 'receipt_long' },
    { key: 'possuiFolhaPagamento', name: 'Folha de Pagamento', icon: 'groups' },
    {
      key: 'possuiBeneficioPrevidencia',
      name: 'Benefício Previdenciário',
      icon: 'volunteer_activism',
    },
    { key: 'possuiDebitoAutomatico', name: 'Débito Automático', icon: 'autorenew' },
  ];

  readonly products = computed(() => {
    const profile = this.profile();

    const produtos = profile.produtos ?? profile;

    return this.productConfig.map((product) => ({
      ...product,
      active: produtos[product.key],
    }));
  });
}
