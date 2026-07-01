import { Service, signal } from '@angular/core';
import { finalize, MonoTypeOperatorFunction } from 'rxjs';

@Service()
export class BaseTrack {
  readonly loading = signal(false);

  track<T>(): MonoTypeOperatorFunction<T> {
    this.loading.set(true);

    return finalize(() => {
      this.loading.set(false);
    });
  }
}
