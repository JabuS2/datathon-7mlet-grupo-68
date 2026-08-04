import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { form, FormField, max, min, required } from '@angular/forms/signals';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';

import { IOnboardingRequest, SegmentoCliente } from '../../interfaces/ionboarding';
import { BaseTrack } from '../../services/base-track';
import { Onboarding } from '../../services/onboarding';
import { ErrorHandler } from '../../utils/error-handler';

/** Faixa de renda anual → valor representativo enviado ao backend (ponto médio). */
interface FaixaRenda {
  label: string;
  valor: number;
}

/** Tempo de banco → meses. */
interface FaixaTempo {
  label: string;
  meses: number;
}

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [FormField],
  templateUrl: './onboarding.html',
})
export class OnboardingComponent {
  private _snackBar = inject(MatSnackBar);
  private onboardingService = inject(Onboarding);
  private baseTrack = inject(BaseTrack);
  private router = inject(Router);
  private errorHandler = inject(ErrorHandler);

  readonly segmentos = [
    { value: SegmentoCliente.Universitario, label: 'Estou começando / sou estudante' },
    { value: SegmentoCliente.Varejo, label: 'Já tenho renda estável' },
    { value: SegmentoCliente.AltaRenda, label: 'Tenho patrimônio para investir' },
  ];

  /**
   * Faixas em vez de campo livre: ninguém sabe a própria renda anual de cabeça, e o modelo
   * usa o **percentil** dela, não o valor exato — a precisão do ponto médio basta.
   */
  readonly faixasRenda: FaixaRenda[] = [
    { label: 'Até R$ 2 mil por mês', valor: 18_000 },
    { label: 'De R$ 2 mil a R$ 5 mil', valor: 42_000 },
    { label: 'De R$ 5 mil a R$ 10 mil', valor: 90_000 },
    { label: 'Acima de R$ 10 mil', valor: 180_000 },
  ];

  readonly faixasTempo: FaixaTempo[] = [
    { label: 'Menos de 6 meses', meses: 3 },
    { label: 'De 6 meses a 2 anos', meses: 15 },
    { label: 'De 2 a 5 anos', meses: 42 },
    { label: 'Mais de 5 anos', meses: 90 },
  ];

  model = signal<IOnboardingRequest>({
    idade: 30,
    segmento: SegmentoCliente.Varejo,
    rendaEstimadaAnualBrl: this.faixasRenda[1].valor,
    tempoRelacionamentoMeses: this.faixasTempo[1].meses,
    possuiCartaoCredito: false,
    possuiFundoInvestimento: false,
    possuiFinanciamentoImovel: false,
  });

  onboardingForm = form(this.model, (path) => {
    required(path.idade, { message: 'Idade é requerida' });
    // os limites ficam no schema, não como atributo do input: o `[formField]` proíbe
    // `min`/`max` no HTML (NG8022) para manter uma única fonte de validação
    min(path.idade, 18, { message: 'É preciso ter ao menos 18 anos' });
    max(path.idade, 100, { message: 'Informe uma idade válida' });
  });

  /** Os `<select>` devolvem string; o backend espera número/enum. */
  setRenda(value: string): void {
    this.model.update((m) => ({ ...m, rendaEstimadaAnualBrl: Number(value) }));
  }

  setTempo(value: string): void {
    this.model.update((m) => ({ ...m, tempoRelacionamentoMeses: Number(value) }));
  }

  setSegmento(value: string): void {
    this.model.update((m) => ({ ...m, segmento: value as SegmentoCliente }));
  }

  toggle(campo: 'possuiCartaoCredito' | 'possuiFundoInvestimento' | 'possuiFinanciamentoImovel'): void {
    this.model.update((m) => ({ ...m, [campo]: !m[campo] }));
  }

  onSubmit(event: Event): void {
    event.preventDefault();

    this.onboardingService
      .completeProfile(this.model())
      .pipe(this.baseTrack.track())
      .subscribe({
        next: () => {
          // a sessão já existe (o guard exige token): não há o que autenticar aqui
          this._snackBar.open('Perfil criado! Veja suas ofertas.', 'Fechar', {
            duration: 3000,
            horizontalPosition: 'end',
            verticalPosition: 'top',
          });
          this.router.navigate(['/dashboard']);
        },
        error: (error: HttpErrorResponse) => {
          this._snackBar.open(this.errorHandler.getErrorMessage(error), 'Fechar', {
            duration: 4000,
            horizontalPosition: 'end',
            verticalPosition: 'top',
          });
        },
      });
  }
}
