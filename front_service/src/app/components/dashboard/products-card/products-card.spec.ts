import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { ProductsCardComponent } from './products-card';
import { IProfileResponse } from '../../../interfaces/iprofile';

describe('ProductsCardComponent', () => {
  let component: ProductsCardComponent;
  let fixture: ComponentFixture<ProductsCardComponent>;

  const profile: IProfileResponse = {
    id: 1,
    codCliente: 123,
    idade: 42,
    tempoRelacionamentoMeses: 24,
    indAtivo: true,
    segmento: 'Premium',
    estado: 'SP',
    segmentosSinteticos: ['Alta Renda Potencial'],
    origem: 'app',
    rendaEstimadaAnualBrl: 1500000.5,
    saldoFicticio: 2500.75,
    produtos: {
      possuiPoupanca: true,
      possuiContaCorrente: false,
      possuiContaCorrentePlus: false,
      possuiContaPremium: false,
      possuiContaSalario: false,
      possuiContaJunior: false,
      possuiContaUniversitaria: false,
      possuiContaDigital: false,
      possuiContaInvestimento: false,
      possuiCdbCurtoPrazo: false,
      possuiCdbMedioPrazo: false,
      possuiCdbLongoPrazo: false,
      possuiFundoInvestimento: false,
      possuiTitulosInvestimento: false,
      possuiPrevidenciaPrivada: false,
      possuiFinanciamentoImovel: false,
      possuiFinanciamentoVeiculo: false,
      possuiEmprestimoPessoal: false,
      possuiCartaoCredito: false,
      possuiAvalGarantia: false,
      possuiPagamentoTributos: false,
      possuiFolhaPagamento: false,
      possuiBeneficioPrevidencia: false,
      possuiDebitoAutomatico: false,
    },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductsCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductsCardComponent);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve renderizar os produtos e o estado ativo/inativo', () => {
    fixture.componentRef.setInput('profile', profile);
    fixture.detectChanges();

    const productRows = fixture.nativeElement.querySelectorAll(
      'div.rounded-md.border.border-gray-200.p-4',
    );

    expect(productRows.length).toBe(24);
    expect(productRows[0].textContent).toContain('Poupança');
    expect(productRows[0].textContent).toContain('Ativo');
    expect(productRows[1].textContent).toContain('Conta Corrente');
    expect(productRows[1].textContent).toContain('Inativo');
  });
});
