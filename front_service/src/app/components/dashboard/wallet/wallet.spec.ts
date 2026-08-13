import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProductCategory } from '../../../interfaces/iinvestiment';
import { Investiment } from '../../../services/investiment';
import { WalletComponent } from './wallet';

describe('WalletComponent', () => {
  let component: WalletComponent;
  let fixture: ComponentFixture<WalletComponent>;

  const item = {
    armId: 'OFF-CR-001',
    productName: 'Crédito Pessoal Pré-Aprovado',
    description: 'Dinheiro na conta em minutos.',
    category: ProductCategory.Credito,
    cliques: 1,
    ultimoClique: '2026-08-04T00:00:00',
  };

  const investimentMock = { interests: vi.fn().mockReturnValue(of([item])) };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [WalletComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Investiment, useValue: investimentMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(WalletComponent);
    component = fixture.componentInstance;
  });

  it('carrega a carteira da API e renderiza o produto', () => {
    fixture.componentRef.setInput('refreshKey', 1);
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(component.itens()).toHaveLength(1);
    expect(texto).toContain('Minha carteira');
    expect(texto).toContain('Crédito Pessoal Pré-Aprovado');
    expect(texto).toContain('1 produto');
  });

  it('mostra o estado vazio explicando como preencher', () => {
    investimentMock.interests.mockReturnValue(of([]));
    fixture.componentRef.setInput('refreshKey', 1);
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Sua carteira está vazia');
    expect(texto).toContain('Tenho interesse');
  });

  it('mostra a contagem de cliques quando há repetição', () => {
    investimentMock.interests.mockReturnValue(of([{ ...item, cliques: 3 }]));
    fixture.componentRef.setInput('refreshKey', 1);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('3 vezes');
  });

  it('plural na contagem de produtos', () => {
    investimentMock.interests.mockReturnValue(
      of([item, { ...item, armId: 'OFF-SEG-001' }]),
    );
    fixture.componentRef.setInput('refreshKey', 1);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('2 produtos');
  });

  it('recarrega quando a chave muda — a fonte é a API, não estado local', () => {
    fixture.componentRef.setInput('refreshKey', 1);
    fixture.detectChanges();
    fixture.componentRef.setInput('refreshKey', 2);
    fixture.detectChanges();

    expect(investimentMock.interests).toHaveBeenCalledTimes(3);
  });
});
