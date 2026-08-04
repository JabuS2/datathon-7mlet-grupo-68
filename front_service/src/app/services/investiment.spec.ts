import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { ProductCategory, RecommendationItem } from '../interfaces/iinvestiment';
import { Investiment } from './investiment';

describe('Investiment', () => {
  let service: Investiment;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [Investiment, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(Investiment);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve fazer GET no endpoint de recomendações', () => {
    const mockResponse: RecommendationItem[] = [
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
        jaAdquirida: false,
      },
    ];

    service.recommendations().subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const request = httpMock.expectOne('http://localhost:8001/api/v1/offers');

    expect(request.request.method).toBe('GET');
    request.flush(mockResponse);
  });

  afterEach(() => {
    httpMock.verify();
  });
});
