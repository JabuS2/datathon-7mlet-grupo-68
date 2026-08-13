import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { Investiment } from '../../../services/investiment';
import { Profile } from '../../../services/profile';

import { InvestimentsComponent } from './investiments-component';

describe('InvestimentsComponent', () => {
  let component: InvestimentsComponent;
  let fixture: ComponentFixture<InvestimentsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InvestimentsComponent],
      providers: [
        provideRouter([]),
        { provide: Profile, useValue: { me: () => of(null) } },
        { provide: Investiment, useValue: { interests: () => of([]) } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(InvestimentsComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
