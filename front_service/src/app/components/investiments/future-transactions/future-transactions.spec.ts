import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FutureTransactionsComponent } from './future-transactions';

describe('FutureTransactionsComponent', () => {
  let component: FutureTransactionsComponent;
  let fixture: ComponentFixture<FutureTransactionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FutureTransactionsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(FutureTransactionsComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
