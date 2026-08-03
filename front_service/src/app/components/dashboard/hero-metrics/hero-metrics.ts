import { Component, input } from '@angular/core';
import { IProfileResponse } from '../../../interfaces/iprofile';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-hero-metrics',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './hero-metrics.html',
})
export class HeroMetricsComponent {
  profile = input.required<IProfileResponse>();
}
