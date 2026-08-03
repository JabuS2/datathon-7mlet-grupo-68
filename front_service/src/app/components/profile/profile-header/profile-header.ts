import { Component, input } from '@angular/core';
import { IProfileResponse } from '../../../interfaces/iprofile';

@Component({
  selector: 'app-profile-header',
  standalone: true,
  templateUrl: './profile-header.html',
})
export class ProfileHeaderComponent {
  profile = input.required<IProfileResponse>();
}
