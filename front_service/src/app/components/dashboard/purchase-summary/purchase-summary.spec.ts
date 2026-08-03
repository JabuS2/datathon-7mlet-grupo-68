import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { PurchaseSummary } from './purchase-summary';

describe('PurchaseSummary', () => {
  let component: PurchaseSummary;
  let fixture: ComponentFixture<PurchaseSummary>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PurchaseSummary],
    }).compileComponents();

    fixture = TestBed.createComponent(PurchaseSummary);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve renderizar as três categorias com suas larguras', () => {
    fixture.detectChanges();

    const categories = fixture.nativeElement.querySelectorAll('span.text-sm.text-gray-500');
    const bars = fixture.nativeElement.querySelectorAll('div.h-full.rounded-full.bg-black');

    expect(component.categories).toHaveLength(3);
    expect(categories[0].textContent).toContain('Alimentação');
    expect(categories[1].textContent).toContain('Lazer & Viagens');
    expect(categories[2].textContent).toContain('Serviços & Contas');
    expect(bars[0].getAttribute('style')).toContain('45%');
    expect(bars[1].getAttribute('style')).toContain('65%');
    expect(bars[2].getAttribute('style')).toContain('25%');
  });
});
