import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { ProfileHeaderComponent } from './profile-header';
import { IProfileResponse } from '../../../interfaces/iprofile';

describe('ProfileHeaderComponent', () => {
  let component: ProfileHeaderComponent;
  let fixture: ComponentFixture<ProfileHeaderComponent>;

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
      imports: [ProfileHeaderComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfileHeaderComponent);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve renderizar o status do cliente', () => {
    fixture.componentRef.setInput('profile', profile);
    fixture.detectChanges();

    const textContent = fixture.nativeElement.textContent as string;

    expect(textContent).toContain('Cliente Ativo');
  });
});
