import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { Register } from '../../services/register';

describe('Register', () => {
  let service: Register;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        Register,
        provideHttpClient()
      ]
    });

    service = TestBed.inject(Register);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});