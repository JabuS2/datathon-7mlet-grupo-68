import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvestmentOpportunitiesComponent } from './investments';
import { Investiment } from '../../../services/investiment';
import { ProductCategory } from '../../../interfaces/iinvestiment';

describe('InvestmentOpportunitiesComponent', () => {
  let component: InvestmentOpportunitiesComponent;
  let fixture: ComponentFixture<InvestmentOpportunitiesComponent>;

  const opportunity = {
    armId: 'ARM-001',
    rank: 1,
    score: 0.8421,
    productName: 'CDB Conservador',
    description: 'Baixo risco para início de carteira.',
    category: ProductCategory.Investimento,
    valorTotal: 1000,
    descontoPct: 5,
    valorFinal: 950,
  };

  const investimentMock = {
    recommendations: vi.fn().mockReturnValue(of([opportunity])),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [InvestmentOpportunitiesComponent],
      providers: [{ provide: Investiment, useValue: investimentMock }],
    }).compileComponents();

    fixture = TestBed.createComponent(InvestmentOpportunitiesComponent);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve carregar recomendações e renderizar o cartão', () => {
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);

    fixture.detectChanges();

    const textContent = fixture.nativeElement.textContent as string;

    expect(investimentMock.recommendations).toHaveBeenCalledOnce();
    expect(component.opportunities()).toHaveLength(1);
    expect(textContent).toContain('Oportunidades para você');
    expect(textContent).toContain('CDB Conservador');

    component.knowMore(opportunity as any);

    expect(logSpy).toHaveBeenCalledWith('Oferta selecionada:', opportunity);
  });
});
