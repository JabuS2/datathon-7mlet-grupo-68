import { DecimalPipe, KeyValuePipe } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { MLFLOW_URL } from '../../core/api';
import {
  IArmState,
  ICicloRetreino,
  IMetricaPublicada,
  IMetricsReport,
  IModeloRegistrado,
  IPolitica,
} from '../../interfaces/igovernance';
import { Account } from '../../services/account';
import { Governance } from '../../services/governance';
import { SidebarComponent } from '../shared/sidebar/sidebar';
import { TopbarComponent } from '../shared/topbar/topbar';

type Aba = 'politicas' | 'ciclos' | 'metricas' | 'mlflow';

/**
 * Console de operação do modelo.
 *
 * "Treinar" não é uma operação aqui: o bandit aprende online, a cada feedback. Retreinar
 * significa registrar uma política nova (nasce `shadow`), deixá-la aprender em paralelo,
 * comparar métricas e promover pelo gate humano. O rollback é instantâneo porque cada
 * política tem sua própria chave de estado no Redis.
 */
@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [SidebarComponent, TopbarComponent, DecimalPipe, KeyValuePipe],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class Admin implements OnInit {
  private governance = inject(Governance);
  private account = inject(Account);
  private sanitizer = inject(DomSanitizer);
  private _snackBar = inject(MatSnackBar);

  aba = signal<Aba>('politicas');
  /** Quem está operando — vai no registro do gate humano. */
  operadorId = signal<number | null>(null);

  politicas = signal<IPolitica[]>([]);
  ciclos = signal<ICicloRetreino[]>([]);
  metricas = signal<IMetricaPublicada[]>([]);
  modelos = signal<IModeloRegistrado[]>([]);

  /** Política cuja lista de braços está aberta. */
  politicaAberta = signal<string | null>(null);
  bracos = signal<IArmState[]>([]);

  /** Apuração ao vivo do api_service para a política selecionada. */
  apuracao = signal<IMetricsReport | null>(null);

  ativa = computed(() => this.politicas().find((p) => p.status === 'active') ?? null);
  candidatos = computed(() => this.ciclos().filter((c) => c.status === 'candidate'));

  /** MLflow embutido. A URL é constante da app, não vem de input do usuário. */
  mlflowUrl: SafeResourceUrl = this.sanitizer.bypassSecurityTrustResourceUrl(MLFLOW_URL);
  readonly mlflowHref = MLFLOW_URL;

  ngOnInit(): void {
    this.account.me().subscribe((me) => this.operadorId.set(me.id));
    this.recarregar();
  }

  trocarAba(aba: Aba): void {
    this.aba.set(aba);
    if (aba === 'mlflow' && !this.modelos().length) this.carregarModelos();
  }

  recarregar(): void {
    this.governance.policies().subscribe({
      next: (p) => this.politicas.set(p),
      error: () => this.falhou('Não foi possível carregar as políticas'),
    });
    this.governance.cycles().subscribe({ next: (c) => this.ciclos.set(c), error: () => void 0 });
    this.governance.publishedMetrics().subscribe({
      next: (m) => this.metricas.set(m),
      error: () => void 0,
    });
  }

  private carregarModelos(): void {
    this.governance.registryModels().subscribe({
      next: (m) => this.modelos.set(m),
      error: () => this.falhou('MLflow não respondeu'),
    });
  }

  verBracos(policyId: string): void {
    if (this.politicaAberta() === policyId) {
      this.politicaAberta.set(null);
      return;
    }
    this.politicaAberta.set(policyId);
    this.governance.arms(policyId).subscribe({
      next: (b) => this.bracos.set(b),
      error: () => this.falhou('Não foi possível ler os pesos'),
    });
  }

  /** Rótulo legível dos parâmetros — variam por algoritmo, de propósito. */
  paramsDe(braco: IArmState): string {
    return Object.entries(braco.params)
      .map(([k, v]) => `${k}: ${v ?? '—'}`)
      .join('  ·  ');
  }

  promover(policyId: string): void {
    this.governance.promote(policyId).subscribe({
      next: () => {
        this.ok(`${policyId} agora é a política ativa`);
        this.recarregar();
      },
      error: () => this.falhou('Falha ao promover'),
    });
  }

  apurar(policyId: string): void {
    this.governance.computeMetrics(policyId).subscribe({
      next: (r) => this.apuracao.set(r),
      error: () => this.falhou('Falha ao apurar — a rota exige token de operador'),
    });
  }

  /** Apura, publica e abre o ciclo — o model_service versiona o modelo no MLflow. */
  abrirCiclo(policyId: string): void {
    this.governance.publishMetrics(policyId).subscribe({
      next: (relatorio) => {
        const metrics = Object.fromEntries(relatorio.metrics.map((m) => [m.name, m.value]));
        this.governance.startCycle(policyId, metrics).subscribe({
          next: (ciclo) => {
            this.ok(
              ciclo.registry_version
                ? `Ciclo ${ciclo.run_id} aberto — modelo versionado (v${ciclo.registry_version})`
                : `Ciclo ${ciclo.run_id} aberto (MLflow fora; o gate não depende dele)`,
            );
            this.recarregar();
          },
          error: () => this.falhou('Falha ao abrir o ciclo'),
        });
      },
      error: () => this.falhou('Falha ao apurar métricas'),
    });
  }

  decidir(runId: string, decisao: 'approve' | 'reject'): void {
    const operadorId = this.operadorId();
    if (operadorId === null) {
      this.falhou('Sem identificação do operador — recarregue a página');
      return;
    }
    this.governance.decide(runId, decisao, operadorId).subscribe({
      next: () => {
        this.ok(decisao === 'approve' ? 'Candidata promovida' : 'Candidata reprovada');
        this.recarregar();
      },
      error: () => this.falhou('Falha no gate'),
    });
  }

  reverter(runId: string): void {
    const alvo = this.politicas().find((p) => p.status === 'retired');
    if (!alvo) {
      this.falhou('Não há política aposentada para onde voltar');
      return;
    }
    this.governance.rollback(runId, alvo.policy_id).subscribe({
      next: () => {
        this.ok(`Revertido para ${alvo.policy_id}`);
        this.recarregar();
      },
      error: () => this.falhou('Falha no rollback'),
    });
  }

  private ok(msg: string): void {
    this._snackBar.open(msg, 'Fechar', {
      duration: 3500,
      horizontalPosition: 'end',
      verticalPosition: 'top',
    });
  }

  private falhou(msg: string): void {
    this._snackBar.open(msg, 'Fechar', {
      duration: 4000,
      horizontalPosition: 'end',
      verticalPosition: 'top',
    });
  }
}
