export interface AppState {
  step: number;
  rawText: string;
  metadata: any;
  lexicalHashOriginal?: string;
  lexicalHashFinal?: string;
  semanticHashOriginal?: string;
  semanticHashFinal?: string;
  semanticHashScore?: number;
  fileName?: string;
}