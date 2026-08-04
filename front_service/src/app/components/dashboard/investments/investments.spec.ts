import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CONFIRMACAO_MS, InvestmentOpportunitiesComponent } from './investments';
import { Investiment } from '../../../services/investiment';
import { Feedback } from '../../../services/feedback';
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

  const feedbackMock = {
    click: vi.fn().mockReturnValue(of({ armId: 'ARM-001', clicked: true, reward: 1 })),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [InvestmentOpportunitiesComponent],
      providers: [
        { provide: Investiment, useValue: investimentMock },
        { provide: Feedback, useValue: feedbackMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(InvestmentOpportunitiesComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    vi.useRealTimers();
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

    logSpy.mockRestore();
  });

  it('clicar no card marca o item e só depois recarrega a vitrine', () => {
    vi.useFakeTimers();
    fixture.detectChanges();
    investimentMock.recommendations.mockClear();

    component.knowMore(opportunity as never);

    // a confirmação vem ANTES do reload: é o que faz o clique parecer ter efeito
    expect(feedbackMock.click).toHaveBeenCalledWith('ARM-001');
    expect(component.escolhido()).toBe('ARM-001');
    expect(investimentMock.recommendations).not.toHaveBeenCalled();

    vi.advanceTimersByTime(CONFIRMACAO_MS);

    expect(investimentMock.recommendations).toHaveBeenCalledOnce();
    expect(component.escolhido()).toBeNull();
    expect(component.enviando()).toBeNull();
    vi.useRealTimers();
  });

  it('emite o evento que faz a carteira recarregar', () => {
    vi.useFakeTimers();
    fixture.detectChanges();
    const emitido: string[] = [];
    component.interesseRegistrado.subscribe((arm) => emitido.push(arm));

    component.knowMore(opportunity as never);

    expect(emitido).toEqual(['ARM-001']);
    vi.useRealTimers();
  });

  it('ignora clique enquanto outro está em voo (evita reward duplicado)', () => {
    fixture.detectChanges();
    component.enviando.set('ARM-002');
    feedbackMock.click.mockClear();

    component.knowMore(opportunity as never);

    expect(feedbackMock.click).not.toHaveBeenCalled();
  });

  it('mostra no máximo o top 4 e expande com "ver mais"', () => {
    const muitas = Array.from({ length: 6 }, (_, i) => ({ ...opportunity, armId: `ARM-${i}` }));
    component.opportunities.set(muitas as never);

    expect(component.visiveis()).toHaveLength(4);
    expect(component.ocultas()).toBe(2);

    component.toggleExpandir();
    expect(component.visiveis()).toHaveLength(6);
    expect(component.ocultas()).toBe(2);
  });

  it('não oferece "ver mais" quando cabe tudo', () => {
    component.opportunities.set([opportunity] as never);
    expect(component.ocultas()).toBe(0);
  });
});
