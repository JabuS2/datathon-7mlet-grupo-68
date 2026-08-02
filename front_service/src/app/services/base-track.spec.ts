import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { BaseTrack } from './base-track';

describe('BaseTrack', () => {
  let service: BaseTrack;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [BaseTrack],
    });

    service = TestBed.inject(BaseTrack);
  });

  it('deve ser criado', () => {
    expect(service).toBeTruthy();
  });

  it('deve definir loading como true enquanto a operação estiver em andamento e false ao completar', () => {
    const subject = new Subject<void>();

    expect(service.loading()).toBe(false);

    subject.pipe(service.track()).subscribe();

    expect(service.loading()).toBe(true);

    subject.complete();

    expect(service.loading()).toBe(false);
  });

  it('deve definir loading como true enquanto a operação estiver em andamento e false ao ocorrer erro', () => {
    const subject = new Subject<void>();

    expect(service.loading()).toBe(false);

    subject.pipe(service.track()).subscribe({
      error: () => {
        expect(service.loading()).toBe(true);
      },
    });

    expect(service.loading()).toBe(true);

    subject.error(new Error('erro'));

    expect(service.loading()).toBe(false);
  });

  afterEach(() => {
    TestBed.resetTestingModule();
  });
});
