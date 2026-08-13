import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RecentTransactions } from './recent-transactions';

describe('RecentTransactions', () => {
  let component: RecentTransactions;
  let fixture: ComponentFixture<RecentTransactions>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RecentTransactions],
    }).compileComponents();

    fixture = TestBed.createComponent(RecentTransactions);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
