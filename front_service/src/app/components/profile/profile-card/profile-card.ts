import { Component, input } from '@angular/core';
import { IProfileResponse } from '../../../interfaces/iprofile';

@Component({
  selector: 'app-profile-card',
  standalone: true,
  templateUrl: './profile-card.html',
})
export class ProfileCardComponent {
  profile = input.required<IProfileResponse>();
}
