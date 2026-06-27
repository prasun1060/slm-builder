import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';

type VectorStoreType = 'chroma' | 'mongodb';

interface ModelRecord {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  description?: string;
}

interface PipelineRecord {
  id: number;
  name: string;
  description?: string;
  model_id: number;
  vector_store_type: VectorStoreType;
  vector_store_config?: Record<string, string>;
  embedding_model: string;
  indexing_status: string;
}

interface DocumentRecord {
  id: number;
  title: string;
  chunk_count: number;
}

interface ChatSource {
  title: string;
  text: string;
  score: number;
}

interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly http = inject(HttpClient);
  private readonly apiBase = 'http://localhost:8000';

  readonly models = signal<ModelRecord[]>([]);
  readonly pipelines = signal<PipelineRecord[]>([]);
  readonly documents = signal<DocumentRecord[]>([]);
  readonly chatSources = signal<ChatSource[]>([]);
  readonly status = signal('Ready');
  readonly error = signal('');
  readonly answer = signal('');
  readonly loading = signal(false);

  readonly modelForm = {
    name: 'Local Llama',
    provider: 'ollama',
    model_id: 'llama3.2',
    description: 'Local Ollama model',
  };

  readonly pipelineForm = {
    name: 'Knowledge pipeline',
    description: 'Local RAG pipeline',
    model_id: 0,
    vector_store_type: 'chroma' as VectorStoreType,
    embedding_model: 'local-hash',
    mongodb_uri: '',
    mongodb_database: '',
    mongodb_collection: '',
    mongodb_index_name: '',
  };

  readonly documentForm = {
    title: 'Notes',
    content: '',
  };

  readonly chatForm = {
    message: '',
  };

  readonly selectedPipelineId = signal<number | null>(null);
  readonly selectedPipeline = computed(() => {
    const id = this.selectedPipelineId();
    return this.pipelines().find((pipeline) => pipeline.id === id) ?? null;
  });

  constructor() {
    this.refreshAll();
  }

  refreshAll(): void {
    this.loadModels();
    this.loadPipelines();
  }

  loadModels(): void {
    this.http.get<ModelRecord[]>(`${this.apiBase}/api/models/`).subscribe({
      next: (models) => {
        this.models.set(models);
        if (!this.pipelineForm.model_id && models.length > 0) {
          this.pipelineForm.model_id = models[0].id;
        }
      },
      error: (error) => this.showError(error),
    });
  }

  loadPipelines(): void {
    this.http.get<PipelineRecord[]>(`${this.apiBase}/api/pipelines/`).subscribe({
      next: (pipelines) => {
        this.pipelines.set(pipelines);
        if (!this.selectedPipelineId() && pipelines.length > 0) {
          this.selectPipeline(pipelines[0].id);
        }
      },
      error: (error) => this.showError(error),
    });
  }

  createModel(): void {
    this.loading.set(true);
    this.http.post<ModelRecord>(`${this.apiBase}/api/models/`, this.modelForm).subscribe({
      next: (model) => {
        this.status.set(`Model created: ${model.name}`);
        this.pipelineForm.model_id = model.id;
        this.loadModels();
        this.loading.set(false);
      },
      error: (error) => this.finishWithError(error),
    });
  }

  createPipeline(): void {
    const vector_store_config =
      this.pipelineForm.vector_store_type === 'mongodb'
        ? {
            uri: this.pipelineForm.mongodb_uri,
            database: this.pipelineForm.mongodb_database,
            collection: this.pipelineForm.mongodb_collection,
            index_name: this.pipelineForm.mongodb_index_name,
          }
        : {};

    const payload = {
      name: this.pipelineForm.name,
      description: this.pipelineForm.description,
      model_id: Number(this.pipelineForm.model_id),
      vector_store_type: this.pipelineForm.vector_store_type,
      vector_store_config,
      embedding_model: this.pipelineForm.embedding_model,
    };

    this.loading.set(true);
    this.http.post<PipelineRecord>(`${this.apiBase}/api/pipelines/`, payload).subscribe({
      next: (pipeline) => {
        this.status.set(`Pipeline created: ${pipeline.name}`);
        this.selectedPipelineId.set(pipeline.id);
        this.loadPipelines();
        this.loading.set(false);
      },
      error: (error) => this.finishWithError(error),
    });
  }

  selectPipeline(id: number): void {
    this.selectedPipelineId.set(id);
    this.answer.set('');
    this.chatSources.set([]);
  }

  addDocument(): void {
    const pipeline = this.selectedPipeline();
    if (!pipeline) {
      this.error.set('Create or select a pipeline first.');
      return;
    }

    this.loading.set(true);
    this.http
      .post<DocumentRecord>(
        `${this.apiBase}/api/rag/pipelines/${pipeline.id}/documents`,
        this.documentForm,
      )
      .subscribe({
        next: (document) => {
          this.documents.update((documents) => [document, ...documents]);
          this.documentForm.content = '';
          this.status.set(`Document added: ${document.title}`);
          this.loading.set(false);
        },
        error: (error) => this.finishWithError(error),
      });
  }

  uploadDocument(event: Event): void {
    const pipeline = this.selectedPipeline();
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!pipeline || !file) {
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    this.loading.set(true);
    this.http
      .post<DocumentRecord>(`${this.apiBase}/api/rag/pipelines/${pipeline.id}/upload`, formData)
      .subscribe({
        next: (document) => {
          this.documents.update((documents) => [document, ...documents]);
          this.status.set(`Uploaded: ${document.title}`);
          this.loading.set(false);
          input.value = '';
        },
        error: (error) => this.finishWithError(error),
      });
  }

  indexPipeline(): void {
    const pipeline = this.selectedPipeline();
    if (!pipeline) {
      this.error.set('Create or select a pipeline first.');
      return;
    }

    this.loading.set(true);
    this.http.post(`${this.apiBase}/api/rag/pipelines/${pipeline.id}/index`, {}).subscribe({
      next: () => {
        this.status.set('Pipeline indexed.');
        this.loadPipelines();
        this.loading.set(false);
      },
      error: (error) => this.finishWithError(error),
    });
  }

  sendMessage(): void {
    const pipeline = this.selectedPipeline();
    if (!pipeline) {
      this.error.set('Create or select a pipeline first.');
      return;
    }

    this.loading.set(true);
    this.answer.set('');
    this.chatSources.set([]);
    this.http
      .post<ChatResponse>(`${this.apiBase}/api/rag/pipelines/${pipeline.id}/chat`, {
        message: this.chatForm.message,
        top_k: 4,
      })
      .subscribe({
        next: (response) => {
          this.answer.set(response.answer);
          this.chatSources.set(response.sources);
          this.status.set('Answer generated.');
          this.loading.set(false);
        },
        error: (error) => this.finishWithError(error),
      });
  }

  private finishWithError(error: unknown): void {
    this.loading.set(false);
    this.showError(error);
  }

  private showError(error: any): void {
    const detail = error?.error?.detail;
    this.error.set(typeof detail === 'string' ? detail : 'Request failed. Is the API running?');
  }
}
