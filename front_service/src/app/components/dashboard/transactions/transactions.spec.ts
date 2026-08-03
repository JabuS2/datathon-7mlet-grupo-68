import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { Transactions } from './transactions';

describe('Transactions', () => {
  let component: Transactions;
  let fixture: ComponentFixture<Transactions>;

  beforeEach(async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.1);

    await TestBed.configureTestingModule({
      imports: [Transactions],
    }).compileComponents();

    fixture = TestBed.createComponent(Transactions);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve gerar quatro transações e renderizar a tabela', () => {
    fixture.detectChanges();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    const headers = fixture.nativeElement.querySelectorAll('thead th');

    expect(component.transactions).toHaveLength(4);
    expect(rows).toHaveLength(4);
    expect(headers[0].textContent).toContain('Data');
    expect(headers[1].textContent).toContain('Descrição');
    expect(headers[2].textContent).toContain('Status');
    expect(headers[3].textContent).toContain('Valor');
    expect(rows[0].textContent).toContain('Pagamento via PIX');
    expect(rows[0].textContent).toContain('Processando');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });
});
