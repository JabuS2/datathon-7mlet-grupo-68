import { Component, input } from '@angular/core';
import { IProfileResponse } from '../../../interfaces/iprofile';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-income-card',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './income-card.html',
})
export class IncomeCardComponent {
  profile = input.required<IProfileResponse>();
}
