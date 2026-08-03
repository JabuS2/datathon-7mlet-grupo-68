import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { SegmentsCardComponent } from './segments-card';

describe('SegmentsCardComponent', () => {
  let component: SegmentsCardComponent;
  let fixture: ComponentFixture<SegmentsCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SegmentsCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SegmentsCardComponent);
    component = fixture.componentInstance;
  });

  it('deve ser criado', () => {
    expect(component).toBeTruthy();
  });

  it('deve renderizar os quatro segmentos', () => {
    fixture.detectChanges();

    const segments = fixture.nativeElement.querySelectorAll('span.px-4.py-2.rounded-full');

    expect(component.segments).toHaveLength(4);
    expect(segments[0].textContent).toContain('Alta Renda Potencial');
    expect(segments[1].textContent).toContain('Digital Heavy User');
    expect(segments[2].textContent).toContain('Crédito Baixo Risco');
    expect(segments[3].textContent).toContain('Propenso a Consórcio');
  });
});
