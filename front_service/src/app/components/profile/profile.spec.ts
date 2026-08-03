import { provideRouter } from '@angular/router';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileComponent } from './profile';
import { IProfileResponse } from '../../interfaces/iprofile';
import { Profile as ProfileService } from '../../services/profile';

describe('ProfileComponent', () => {
  let component: ProfileComponent;
  let fixture: ComponentFixture<ProfileComponent>;

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

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [ProfileComponent],
      providers: [provideRouter([]), { provide: ProfileService, useValue: profileServiceMock }],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfileComponent);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve carregar o perfil e renderizar os blocos principais', () => {
    fixture.detectChanges();
    fixture.detectChanges();

    expect(profileServiceMock.me).toHaveBeenCalledOnce();
    expect(component.profile()).toEqual(profile);

    const textContent = fixture.nativeElement.textContent as string;

    expect(textContent).toContain('HP Invest - Pro');
    expect(textContent).toContain('Perfil');
    expect(textContent).toContain('Saldo Total');
    expect(textContent).toContain('Renda Anual Projetada');
  });
});
