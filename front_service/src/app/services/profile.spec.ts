import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { IProfileResponse } from '../interfaces/iprofile';
import { Profile } from './profile';

describe('Profile', () => {
  let service: Profile;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Profile, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(Profile);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve fazer GET no endpoint de perfil', () => {
    const mockResponse: IProfileResponse = {
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

    service.me().subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const request = httpMock.expectOne('http://localhost:8008/api/v1/me/profile');

    expect(request.request.method).toBe('GET');
    request.flush(mockResponse);
  });

  afterEach(() => {
    httpMock.verify();
  });
});
