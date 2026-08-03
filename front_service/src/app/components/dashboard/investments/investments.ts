import { Component, inject, OnInit, signal } from '@angular/core';
import { Investiment } from '../../../services/investiment';
import { RecommendationItem } from '../../../interfaces/iinvestiment';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-investments',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './investments.html',
})
export class InvestmentOpportunitiesComponent implements OnInit {
  private investimentService = inject(Investiment);

  opportunities = signal<RecommendationItem[]>([]);

  ngOnInit(): void {
    this.investimentService.recommendations().subscribe((response) => {
      this.opportunities.set(response);
    });
  }

  knowMore(opportunity: RecommendationItem): void {
    console.log('Oferta selecionada:', opportunity);
  }
}
