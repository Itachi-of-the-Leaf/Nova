export interface AppState {
  rawText: string;
  metadata: any; 
  lexicalHashOriginal?: string;
  lexicalHashFinal?: string;
  semanticHashOriginal?: string;
  semanticHashFinal?: string;
  semanticHashScore?: number;
  fileName?: string;
}