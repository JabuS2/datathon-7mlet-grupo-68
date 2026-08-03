import { Component } from '@angular/core';

@Component({
  selector: 'app-segments-card',
  standalone: true,
  templateUrl: './segments-card.html',
})
export class SegmentsCardComponent {
  segments = [
    'Alta Renda Potencial',
    'Digital Heavy User',
    'Crédito Baixo Risco',
    'Propenso a Consórcio',
  ];
}
