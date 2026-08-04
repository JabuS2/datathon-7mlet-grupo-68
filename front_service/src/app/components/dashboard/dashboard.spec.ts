import { provideRouter } from '@angular/router';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { DashboardComponent } from './dashboard';
import { IProfileResponse } from '../../interfaces/iprofile';
import { Profile } from '../../services/profile';
import { Investiment } from '../../services/investiment';
import { ProductCategory } from '../../interfaces/iinvestiment';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

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

  const profileServiceMock = {
    me: vi.fn().mockReturnValue(of(profile)),
  };

  const investimentServiceMock = {
    // a carteira lê daqui também (WalletComponent)
    interests: vi.fn().mockReturnValue(of([])),
    recommendations: vi.fn().mockReturnValue(
      of([
        {
          armId: 'ARM-001',
          rank: 1,
          score: 0.8421,
          productName: 'CDB Conservador',
          description: 'Baixo risco para início de carteira.',
          category: ProductCategory.Investimento,
          valorTotal: 1000,
          descontoPct: 5,
          valorFinal: 950,
        },
      ]),
    ),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideRouter([]),
        { provide: Profile, useValue: profileServiceMock },
        { provide: Investiment, useValue: investimentServiceMock },
      ],
    });

    await TestBed.compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve carregar o perfil e renderizar os cards dependentes', () => {
    fixture.detectChanges();
    fixture.detectChanges();

    expect(profileServiceMock.me).toHaveBeenCalledOnce();
    expect(component.profile()).toEqual(profile);

    const textContent = fixture.nativeElement.textContent as string;

    expect(textContent).toContain('HP Invest - Dashboard');
    expect(textContent).toContain('Saldo Total');
    expect(textContent).toContain('Relacionamento');
    expect(textContent).toContain('Oportunidades para você');
    expect(textContent).toContain('Transações Recentes');
    expect(investimentServiceMock.recommendations).toHaveBeenCalledOnce();
  });

  it('atualiza o saldo exibido com o valor que o servidor devolveu', () => {
    fixture.detectChanges();
    const antes = component.profile()?.saldoFicticio;

    component.aoRegistrarInteresse({ armId: 'ARM-001', saldo: 1234.5 });

    expect(component.profile()?.saldoFicticio).toBe(1234.5);
    expect(component.profile()?.saldoFicticio).not.toBe(antes);
  });

  it('ignora saldo nulo (conta sem saldo definido)', () => {
    fixture.detectChanges();
    const antes = component.profile()?.saldoFicticio;

    component.aoRegistrarInteresse({ armId: 'ARM-001', saldo: null });

    expect(component.profile()?.saldoFicticio).toBe(antes);
  });
});
