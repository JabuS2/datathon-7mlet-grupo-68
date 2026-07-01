import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { Login } from '../../services/login';

describe('Login', () => {
  let service: Login;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        Login,
        provideHttpClient(),
      ],
    });

    service = TestBed.inject(Login);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});